#!/usr/bin/env python3
"""Trusted main-only issue writer; stdlib only, no scanner or dependency execution."""
import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import urllib.error
import urllib.request

REPOSITORY='amazen33/EdgePulse'
TITLE='Supply-chain scan: open findings'
WATCH_TITLE='Upstream updates available'


def request(url,token,payload=None,method=None):
    headers={'Authorization':'Bearer '+token,'User-Agent':'Twinfra-supply-chain-report','Accept':'application/vnd.github+json'}
    value=urllib.request.Request(url,headers=headers,method=method,
                                 data=json.dumps(payload).encode() if payload is not None else None)
    with urllib.request.urlopen(value,timeout=60) as response:return json.load(response)


def publish(report,title,url,token):
    if title not in (TITLE,WATCH_TITLE):raise ValueError('Unexpected issue title')
    if not re.fullmatch(r'https://github.com/amazen33/EdgePulse/actions/runs/[0-9]+',url):raise ValueError('Invalid run URL')
    body=report['markdown']
    if title==TITLE:
        state=report['firstSeen']
        if not isinstance(state,dict) or any(not re.fullmatch(r'[a-f0-9]{64}',key) for key in state):
            raise ValueError('Invalid first-seen state')
        # Losslessly dictionary-code repeated artifact/package/version/CVE/date
        # strings, rather than storing thousands of uncompressible SHA256 keys.
        strings=[];lookup={};records=[];legacy={}
        identities=report.get('identityState',{})
        def index(value):
            if value not in lookup:lookup[value]=len(strings);strings.append(value)
            return lookup[value]
        for key,first in sorted(state.items()):
            fields=identities.get(key)
            if fields is None:legacy[key]=first;continue
            if len(fields)!=4 or not all(isinstance(v,str) for v in fields):raise ValueError('Invalid finding identity')
            if hashlib.sha256(json.dumps(fields,separators=(',',':')).encode()).hexdigest()!=key:
                raise ValueError('Finding identity hash mismatch')
            records.append([index(v) for v in [*fields,first]])
        wire=dict(format=1,strings=strings,records=records,legacy=legacy)
        tail='\n<!-- twinfra-supply-chain-state:'+base64.b64encode(gzip.compress(
            json.dumps(wire,sort_keys=True,separators=(',',':')).encode(),mtime=0)).decode()+' -->\n'
    else:tail=''
    budget=64000-len(tail)-len(url)-100
    if budget<1000:raise ValueError('Tracking state exceeds issue limit')
    if len(body)>budget:body=body[:budget].rsplit('\n',1)[0]+'\n\nFull findings are in the run artifact.\n'
    body=body+'\nRun: '+url+'\n'+tail
    # Labels are issue metadata. Creation is deferred to this main-only issues:write job.
    label_url=f'https://api.github.com/repos/{REPOSITORY}/labels'
    try:request(label_url+'/security',token)
    except urllib.error.HTTPError as error:
        if error.code!=404:raise
        request(label_url,token,dict(name='security',color='b60205',description='Supply-chain vulnerability findings'),'POST')
    matches=[];endpoint=f'https://api.github.com/repos/{REPOSITORY}/issues'
    for page in range(1,11):
        values=request(endpoint+f'?state=all&per_page=100&page={page}',token)
        matches.extend(v for v in values if v.get('title')==title and 'pull_request' not in v)
        if len(values)<100:break
    if len(matches)>1:raise ValueError('Duplicate tracking issues; owner must resolve')
    if matches and (matches[0].get('user',{}).get('login','').lower() not in ('amazen33','github-actions[bot]') or
                    not any(v.get('name')=='security' for v in matches[0].get('labels',[]))):
        raise ValueError('Untrusted reserved tracking issue; owner review required')
    payload=dict(title=title,body=body,labels=['security'],state='open')
    value=request(endpoint+'/'+str(matches[0]['number']) if matches else endpoint,token,payload,
                  'PATCH' if matches else 'POST')
    return value['html_url']


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True);parser.add_argument('--title',required=True)
    parser.add_argument('--run-url',required=True);args=parser.parse_args()
    if os.environ.get('GITHUB_REF')!='refs/heads/main' or os.environ.get('GITHUB_REPOSITORY')!=REPOSITORY:
        raise ValueError('Issue reporting is restricted to trusted main in EdgePulse')
    print(publish(json.loads(args.report.read_text(encoding='utf-8')),args.title,args.run_url,os.environ['GH_TOKEN']))


if __name__=='__main__':main()
