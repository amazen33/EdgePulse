/* IOT-WO-06 ruling 2026-10-21: use the pinned Maven model builder itself.
 * Offline, read-only model resolution; no goals, plugins or scanned code run.
 * Capture every import (including nested imports and inherited models), rather
 * than infer BOM inputs from the flattened effective dependency management.
 */
import java.nio.file.*;
import java.util.*;
import javax.xml.stream.*;
import org.apache.maven.model.*;
import org.apache.maven.model.building.*;
import org.apache.maven.model.resolution.*;

public class ImportedBoms {
    static class Resolver implements ModelResolver {
        final Path cache;
        final SortedMap<String, Path> imports = new TreeMap<>();
        final SortedMap<String, Path> sources = new TreeMap<>();
        Resolver(Path cache) { this.cache = cache; }
        private ModelSource cached(String g, String a, String v) throws UnresolvableModelException {
            if (List.of(g, a, v).stream().anyMatch(s -> !s.matches("[A-Za-z0-9_.+-]+")))
                throw new UnresolvableModelException("Non-exact model coordinate", g, a, v);
            Path file = cache.resolve(g.replace('.', '/') + "/" + a + "/" + v + "/" + a + "-" + v + ".pom");
            if (!Files.isRegularFile(file))
                throw new UnresolvableModelException("Model not resolved by gated Maven build", g, a, v);
            sources.put(g + ":" + a + ":" + v, file);
            return new FileModelSource(file.toFile());
        }
        public ModelSource resolveModel(String g, String a, String v) throws UnresolvableModelException {
            // Maven 3.9's import path calls this overload; parent resolution
            // calls the Parent overload below and must not become an import.
            ModelSource result = cached(g, a, v);
            imports.put(g + ":" + a + ":" + v, sources.get(g + ":" + a + ":" + v));
            return result;
        }
        public ModelSource resolveModel(Parent p) throws UnresolvableModelException {
            return cached(p.getGroupId(), p.getArtifactId(), p.getVersion());
        }
        public ModelSource resolveModel(Dependency d) throws UnresolvableModelException {
            ModelSource result = resolveModel(d.getGroupId(), d.getArtifactId(), d.getVersion());
            imports.put(d.getGroupId() + ":" + d.getArtifactId() + ":" + d.getVersion(),
                        sources.get(d.getGroupId() + ":" + d.getArtifactId() + ":" + d.getVersion()));
            return result;
        }
        public void addRepository(Repository r) { /* Cache only. No repository access. */ }
        public void addRepository(Repository r, boolean replace) { /* Cache only. */ }
        public ModelResolver newCopy() { return this; }
    }
    static ModelBuildingResult build(Path pom, Resolver resolver) throws Exception {
        return new DefaultModelBuilderFactory().newInstance().build(new DefaultModelBuildingRequest()
            .setPomFile(pom.toFile()).setModelResolver(resolver)
            .setSystemProperties(System.getProperties()).setProcessPlugins(false)
            // Match Maven's dependency-descriptor/import validation. Reactor
            // validation is enforced by mvn verify and effective-model equality.
            .setValidationLevel(ModelBuildingRequest.VALIDATION_LEVEL_MINIMAL));
    }
    static void attribute(XMLStreamWriter xml, String name, String value) throws Exception {
        xml.writeAttribute(name, value == null ? "" : value);
    }
    public static void main(String[] args) throws Exception {
        Resolver resolver = new Resolver(Path.of(args[0]));
        XMLStreamWriter xml = XMLOutputFactory.newFactory().createXMLStreamWriter(System.out, "UTF-8");
        xml.writeStartDocument("UTF-8", "1.0"); xml.writeStartElement("models");
        for (int i = 1; i < args.length; i++) {
            Model model = build(Path.of(args[i]), resolver).getEffectiveModel();
            xml.writeStartElement("project"); attribute(xml, "pom", args[i]);
            if (model.getDependencyManagement() != null) {
                for (Dependency d : model.getDependencyManagement().getDependencies()) {
                    xml.writeEmptyElement("managed");
                    attribute(xml,"groupId",d.getGroupId()); attribute(xml,"artifactId",d.getArtifactId());
                    attribute(xml,"version",d.getVersion()); attribute(xml,"type",d.getType());
                    attribute(xml,"classifier",d.getClassifier()); attribute(xml,"scope",d.getScope());
                }
            }
            xml.writeEndElement();
        }
        // Building an imported model also discovers its inherited/nested inputs.
        Set<String> done = new HashSet<>();
        while (!done.containsAll(resolver.imports.keySet())) {
            for (String key : new ArrayList<>(resolver.imports.keySet())) {
                if (!done.add(key)) continue;
                ModelBuildingResult result = build(resolver.imports.get(key), resolver);
                Model model = result.getEffectiveModel();
                if (!"pom".equals(model.getPackaging()))
                    throw new IllegalStateException("Imported BOM is not POM-only: " + key);
                xml.writeStartElement("bom"); attribute(xml,"coordinates",key);
                attribute(xml,"pom",resolver.imports.get(key).toString());
                for (License license : model.getLicenses()) {
                    xml.writeEmptyElement("license"); attribute(xml,"name",license.getName());
                    attribute(xml,"url",license.getUrl());
                }
                xml.writeEndElement();
            }
        }
        for (var source : resolver.sources.entrySet()) {
            xml.writeEmptyElement("source"); attribute(xml,"coordinates",source.getKey());
            attribute(xml,"pom",source.getValue().toString());
        }
        xml.writeEndElement(); xml.writeEndDocument(); xml.flush();
    }
}
