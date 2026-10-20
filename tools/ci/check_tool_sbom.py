"""Real pinned actionlint extraction/Syft/Grype regression; never executes the input."""
import argparse
from pathlib import Path

import supply_chain as sc
from supply_chain_watch import pinned_tool


def check(root,staged,out):
    out.mkdir(parents=True,exist_ok=True)
    tools=sc.verify_tools(staged/'bin',root)
    artifact=sc.read(root/'tools/ci/toolchain.lock.json')['artifacts']['actionlint']
    item=pinned_tool('actionlint',artifact,(staged/'downloads/actionlint').read_bytes(),out)
    binary=Path(item['source'].removeprefix('file:')).read_bytes()
    if (len(binary)<64 or binary[:6]!=b'\x7fELF\x02\x01' or
        int.from_bytes(binary[18:20],'little')!=62):
        raise ValueError('Pinned actionlint input is not an ELF64 Linux amd64 binary')
    plan={'images':[item],'lockfiles':[],'coverage':[],'base':None}
    sc.scan(plan,tools,out/'cache',out,root)
    key=item['digest'].split(':')[1]
    sbom=sc.read(out/'sboms'/(key+'.syft.json'))
    modules=[v for v in sbom.get('artifacts',[]) if v.get('type')=='go-module']
    if sbom.get('source',{}).get('type')!='file' or not modules:
        raise ValueError('Pinned actionlint SBOM must catalog the file and its Go modules')
    grype=sc.read(out/(key+'.grype.json'))
    if not isinstance(grype.get('matches'),list):
        raise ValueError('Pinned actionlint Grype result is missing matches')
    result={'status':'passed','target':item['target'],'archiveSHA256':artifact['sha256'],
            'binarySHA256':key,'goModuleCount':len(modules),'grypeMatchCount':len(grype['matches'])}
    sc.write(out/'tool-regression.json',result)
    print('Pinned actionlint: verified ELF64; Syft Go modules '+str(len(modules))+
          '; valid Grype result ('+str(len(grype['matches']))+' matches).')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=sc.ROOT)
    parser.add_argument('--staged',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    try:check(args.root.resolve(),args.staged.resolve(),args.out.resolve())
    except (ValueError,OSError,KeyError):
        parser.exit(1,'Pinned actionlint regression failed; inspect the restricted diagnostic artifact.\n')
