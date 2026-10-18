package com.edgepulse.platform.identity.architecture;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.edgepulse.platform.architecture.ArchRules;
import com.edgepulse.platform.architecture.ImportHelper;
import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.lang.ArchRule;
import com.tngtech.archunit.lang.EvaluationResult;
import org.junit.jupiter.api.Test;

/**
 * ArchUnit boundary gates for {@code services.identity} (ADR 0012
 * Decision 6, ADR 0013 Decisions 1/2/5/6/8). Every rule here is built
 * from the shared factories in {@code com.edgepulse.platform.architecture}
 * ({@code edgepulse-architecture}, a test-scope-only artifact per ADR 0013
 * Decision 8) with this service's own package names -- this class is
 * where {@code services.identity} states which rules apply to it, not
 * where rule text lives. Vendor-SDK and persistence-provider denylists
 * live in the sibling {@code IdentityFrameworkFreedomArchitectureRulesTest}
 * instead (mirrors this platform's pre-ADR-0013 {@code common} module
 * split between its services.*-isolation test and its own framework-
 * freedom test).
 *
 * <p>Five rules, each with a "holds for real code" check (via
 * {@link ImportHelper#importProductionClasses}) and a negative test that
 * proves the rule actually fires (via
 * {@link ImportHelper#importFixturePackages}), the same two-scan
 * discipline this platform has used since {@code common}'s original
 * architecture tests:
 *
 * <ol>
 *   <li>{@code services.identity.application} must stay framework-free
 *       (no {@code org.springframework..}, {@code jakarta.servlet..}, or
 *       {@code jakarta.ws.rs..}). Formerly the {@code core} rule; step C1
 *       (ADR 0017) renamed {@code core} to {@code application}. The
 *       hexagon's dependency-direction rules live in
 *       {@code IdentityHexagonalArchitectureRulesTest}.</li>
 *   <li>{@code services.identity.rbac} must stay framework-free, same
 *       denylist. RBAC is authorization business logic (ADR 0013
 *       Decision 1: it is exactly the kind of code that must not become
 *       a shared runtime library), and keeping it framework-free is
 *       what makes it safely copyable into a future service's own
 *       package without dragging a framework dependency along with
 *       it.</li>
 *   <li>{@code services.identity.domain} must stay framework-free, same
 *       denylist -- previously unguarded (the domain layer is the one
 *       CLAUDE.md names first as "pure domain core", and had no rule of
 *       its own).</li>
 *   <li>{@code services.identity} must not depend on any sibling bounded
 *       context named in ADR 0012 Decision 6. Currently vacuously true:
 *       none of billing/firmware/evidence/gateway/deployment_studio
 *       exist as Java packages yet (see
 *       {@link #allFiveSiblingIsolationRulesAreCurrentlyVacuous()}).
 *       Siblings are matched by this platform's real top-level package
 *       convention ({@code com.edgepulse.platform.<ctx>}), not a
 *       {@code "..services.."}-shaped guess -- the earlier guess could
 *       never have matched real sibling code, so its own negative test
 *       only ever proved itself against a fixture shaped to fit the
 *       guess (see {@code FakeBillingClass}'s Javadoc).</li>
 *   <li>No class in this service's own build may reside in a retired
 *       shared package ({@code com.edgepulse.platform.common..},
 *       {@code com.edgepulse.platform.adapters.webspring..}) -- the ADR
 *       0013 Decision 5.2 autonomy tripwire, a source-level defense
 *       against reintroducing the exact shared-runtime anti-pattern
 *       ADR 0013 retired, catching it even without a matching
 *       {@code pom.xml} dependency declaration (the Maven Enforcer
 *       {@code bannedDependencies} rule in the parent {@code pom.xml}
 *       is the dependency-declaration-level defense; this rule is the
 *       source-level one). This rule's production scan deliberately
 *       covers the WHOLE {@code com.edgepulse.platform} namespace as
 *       compiled into this module (not just {@code BASE_PACKAGE}) --
 *       see {@link #importWholeModuleProductionClasses()}'s Javadoc for
 *       why the narrower scan could never have caught a real
 *       violation.</li>
 * </ol>
 */
class IdentityArchitectureRulesTest {

    private static final String BASE_PACKAGE = "com.edgepulse.platform.identity";

    /**
     * The umbrella namespace this whole platform builds under. Used
     * only by {@link #importWholeModuleProductionClasses()} -- every
     * other rule in this class deliberately scans just {@link
     * #BASE_PACKAGE}, since those rules are about what THIS service's
     * own code depends on, not about what package a class resides in.
     */
    private static final String PLATFORM_ROOT_PACKAGE = "com.edgepulse.platform";

    private static final String[] FRAMEWORK_DENYLIST = {
            "org.springframework..", "jakarta.servlet..", "jakarta.ws.rs.."
    };

    // Fully-qualified sibling-context package roots, per this platform's
    // real convention (com.edgepulse.platform.<ctx>) -- see this class's
    // Javadoc and ArchRules.noClassesDependOnSiblingBoundedContexts's
    // Javadoc for why this must NOT be a bare context name combined with
    // a "..services.." guess.
    private static final String[] SIBLING_CONTEXTS = {
            "com.edgepulse.platform.billing",
            "com.edgepulse.platform.firmware",
            "com.edgepulse.platform.evidence",
            "com.edgepulse.platform.gateway",
            "com.edgepulse.platform.deployment_studio"
    };

    private static final String[] RETIRED_SHARED_PACKAGES = {
            "com.edgepulse.platform.common..", "com.edgepulse.platform.adapters.webspring.."
    };

    private static JavaClasses importIdentityModule() {
        return ImportHelper.importProductionClasses(BASE_PACKAGE);
    }

    /**
     * Imports every PRODUCTION class compiled into this module's own
     * {@code target/classes} under the whole {@code com.edgepulse.platform}
     * namespace, not just {@link #BASE_PACKAGE}. Maven module boundaries
     * mean this can only ever see this module's own compiled main-source
     * output plus whatever it legitimately depends on that also lives
     * under this namespace (this module's own generated Protobuf classes
     * under {@code com.edgepulse.platform.contracts..}, and, at test scope
     * only, {@code edgepulse-architecture}'s own {@code
     * com.edgepulse.platform.architecture..} classes -- neither is on {@link
     * #RETIRED_SHARED_PACKAGES}, so neither can cause a false failure
     * here).
     *
     * <p>{@link #importIdentityModule()} alone is NOT sufficient for the
     * retired-shared-package tripwire: {@code ClassFileImporter
     * .importPackages(BASE_PACKAGE)} filters by package PREFIX, so a
     * class placed under {@code com.edgepulse.platform.common} -- the exact
     * violation the tripwire exists to catch -- would never be imported
     * in the first place, and the "rule holds for real code" check would
     * pass no matter what was pasted back into this module, having
     * checked nothing. This wider scan is what actually lets the
     * violation be seen and the rule fire on it.
     */
    private static JavaClasses importWholeModuleProductionClasses() {
        return ImportHelper.importProductionClasses(PLATFORM_ROOT_PACKAGE);
    }

    private static ArchRule identityApplicationMustStayFrameworkFree() {
        return ArchRules.noClassesDependOnPackages(
                BASE_PACKAGE + ".application",
                "services.identity.application implements the inbound ports with plain Java "
                        + "(ADR 0017 Decision 2); Spring/servlet/JAX-RS types belong in the driving "
                        + "adapters and the config composition root.",
                FRAMEWORK_DENYLIST);
    }

    private static ArchRule identityRbacMustStayFrameworkFree() {
        return ArchRules.noClassesDependOnPackages(
                BASE_PACKAGE + ".rbac",
                "services.identity.rbac is authorization business logic (ADR 0013 Decision 1); "
                        + "keeping it framework-free is what makes it safely copyable into a future "
                        + "service's own package (ADR 0013's accepted-duplication model) without also "
                        + "copying a framework dependency it never needed.",
                FRAMEWORK_DENYLIST);
    }

    private static ArchRule identityDomainMustStayFrameworkFree() {
        return ArchRules.noClassesDependOnPackages(
                BASE_PACKAGE + ".domain",
                "services.identity.domain is the pure domain core CLAUDE.md's Architectural "
                        + "principles names first; it must stay as framework-free as application/ and rbac/, "
                        + "and previously had no rule of its own.",
                FRAMEWORK_DENYLIST);
    }

    private static ArchRule identityMustNotDependOnSiblingContexts() {
        return ArchRules.noClassesDependOnSiblingBoundedContexts(
                BASE_PACKAGE,
                "services.identity is its own bounded context (ADR 0012 Decision 6); it may "
                        + "depend on its own packages and on ordinary third-party libraries, and on "
                        + "nothing under any sibling context's real package root.",
                SIBLING_CONTEXTS);
    }

    private static ArchRule noClassesResideInRetiredSharedPackages() {
        return ArchRules.noClassesResideInRetiredSharedPackages(
                "ADR 0013 retired common/ and adapters/web-spring/ as shared runtime modules; "
                        + "this is the autonomy tripwire that catches either one being reintroduced at "
                        + "the source level, with or without a matching pom.xml dependency.",
                RETIRED_SHARED_PACKAGES);
    }

    @Test
    void identityApplicationDoesNotDependOnSpring() {
        identityApplicationMustStayFrameworkFree().check(importIdentityModule());
    }

    @Test
    void identityApplicationFrameworkFreedomRuleActuallyCatchesAViolation() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.application.fixtures",
                "org.springframework.web.bind.annotation");

        EvaluationResult result = identityApplicationMustStayFrameworkFree().evaluate(fixtureClasses);

        assertFalse(result.getFailureReport().isEmpty(),
                "the fixture class deliberately depends on a Spring-package stand-in; if this is "
                        + "empty, the application framework-freedom rule is not actually being enforced");
        assertTrue(
                result.getFailureReport().toString().contains("org.springframework"),
                () -> "expected the failure report to name org.springframework, got: "
                        + result.getFailureReport());
    }

    @Test
    void theIdentityApplicationFrameworkFreedomFixtureViolationWouldFailIfRunAsARealAssertion() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.application.fixtures",
                "org.springframework.web.bind.annotation");

        assertThrows(AssertionError.class, () -> identityApplicationMustStayFrameworkFree().check(fixtureClasses));
    }

    @Test
    void identityRbacDoesNotDependOnSpring() {
        identityRbacMustStayFrameworkFree().check(importIdentityModule());
    }

    @Test
    void identityRbacFrameworkFreedomRuleActuallyCatchesAViolation() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.rbac.fixtures",
                "org.springframework.stereotype");

        EvaluationResult result = identityRbacMustStayFrameworkFree().evaluate(fixtureClasses);

        assertFalse(result.getFailureReport().isEmpty(),
                "the fixture class deliberately depends on a Spring-package stand-in; if this is "
                        + "empty, the rbac framework-freedom rule is not actually being enforced");
        assertTrue(
                result.getFailureReport().toString().contains("org.springframework"),
                () -> "expected the failure report to name org.springframework, got: "
                        + result.getFailureReport());
    }

    @Test
    void theIdentityRbacFrameworkFreedomFixtureViolationWouldFailIfRunAsARealAssertion() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.rbac.fixtures",
                "org.springframework.stereotype");

        assertThrows(AssertionError.class, () -> identityRbacMustStayFrameworkFree().check(fixtureClasses));
    }

    @Test
    void identityDomainDoesNotDependOnSpring() {
        identityDomainMustStayFrameworkFree().check(importIdentityModule());
    }

    @Test
    void identityDomainFrameworkFreedomRuleActuallyCatchesAViolation() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.domain.fixtures",
                "org.springframework.web.bind.annotation");

        EvaluationResult result = identityDomainMustStayFrameworkFree().evaluate(fixtureClasses);

        assertFalse(result.getFailureReport().isEmpty(),
                "the fixture class deliberately depends on a Spring-package stand-in; if this is "
                        + "empty, the domain framework-freedom rule is not actually being enforced");
        assertTrue(
                result.getFailureReport().toString().contains("org.springframework"),
                () -> "expected the failure report to name org.springframework, got: "
                        + result.getFailureReport());
    }

    @Test
    void theIdentityDomainFrameworkFreedomFixtureViolationWouldFailIfRunAsARealAssertion() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.domain.fixtures",
                "org.springframework.web.bind.annotation");

        assertThrows(AssertionError.class, () -> identityDomainMustStayFrameworkFree().check(fixtureClasses));
    }

    @Test
    void identityDoesNotDependOnAnySiblingBoundedContext() {
        identityMustNotDependOnSiblingContexts().check(importIdentityModule());
    }

    @Test
    void allFiveSiblingIsolationRulesAreCurrentlyVacuous() {
        // None of billing/firmware/evidence/gateway/deployment_studio exist as
        // Java packages yet -- this test fails, forcing this class's Javadoc to
        // be revisited, the day any of them is added.
        JavaClasses classes = importIdentityModule();
        for (String siblingPackageRoot : SIBLING_CONTEXTS) {
            boolean anyDependencyOnSibling = classes.stream()
                    .anyMatch(javaClass -> javaClass.getDirectDependenciesFromSelf().stream()
                            .anyMatch(dependency ->
                                    dependency.getTargetClass().getPackageName().startsWith(siblingPackageRoot)));
            assertFalse(anyDependencyOnSibling,
                    "expected no dependency on " + siblingPackageRoot + " yet -- if this now fails, "
                            + "the isolation rule for it is no longer vacuous and this test (and the "
                            + "class Javadoc) should be updated to say so");
        }
    }

    @Test
    void identityMustNotDependOnSiblingContextsRuleActuallyCatchesAViolation() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.architecture.fixtures",
                "com.edgepulse.platform.billing");

        EvaluationResult result = identityMustNotDependOnSiblingContexts().evaluate(fixtureClasses);

        assertFalse(result.getFailureReport().isEmpty(),
                "the fixture package deliberately violates the rule; if this is empty, "
                        + "the rule is not actually being enforced");
        assertTrue(
                result.getFailureReport().toString().contains("com.edgepulse.platform.billing"),
                () -> "expected the failure report to name the forbidden com.edgepulse.platform.billing "
                        + "package, got: " + result.getFailureReport());
    }

    @Test
    void theSiblingContextFixtureViolationWouldFailIfRunAsARealAssertion() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.identity.architecture.fixtures",
                "com.edgepulse.platform.billing");

        assertThrows(AssertionError.class, () -> identityMustNotDependOnSiblingContexts().check(fixtureClasses));
    }

    @Test
    void noProductionClassResidesInARetiredSharedPackage() {
        noClassesResideInRetiredSharedPackages().check(importWholeModuleProductionClasses());
    }

    @Test
    void retiredSharedPackageTripwireRuleActuallyCatchesAViolation() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.common.rbac");

        EvaluationResult result = noClassesResideInRetiredSharedPackages().evaluate(fixtureClasses);

        assertFalse(result.getFailureReport().isEmpty(),
                "the fixture class deliberately resides in the retired com.edgepulse.platform.common.rbac "
                        + "package; if this is empty, the autonomy tripwire is not actually being "
                        + "enforced");
        assertTrue(
                result.getFailureReport().toString().contains("com.edgepulse.platform.common.rbac"),
                () -> "expected the failure report to name the retired com.edgepulse.platform.common.rbac "
                        + "package, got: " + result.getFailureReport());
    }

    @Test
    void theRetiredSharedPackageFixtureViolationWouldFailIfRunAsARealAssertion() {
        JavaClasses fixtureClasses = ImportHelper.importFixturePackages(
                "com.edgepulse.platform.common.rbac");

        assertThrows(AssertionError.class, () -> noClassesResideInRetiredSharedPackages().check(fixtureClasses));
    }
}
