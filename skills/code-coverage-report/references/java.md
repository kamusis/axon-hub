# Java Coverage Reference

Use this reference for Java projects using Maven or Gradle.

## Detection

Look for:

- `pom.xml` for Maven.
- `build.gradle` or `build.gradle.kts` for Gradle.
- Existing JaCoCo, Cobertura, IntelliJ, or Sonar coverage configuration.
- CI steps that run tests or publish coverage.

Prefer repository scripts such as `make test`, `./gradlew check`, or documented commands when they exist.

## Common Tools

JaCoCo is the default modern Java coverage tool.

Common Maven plugin:

```xml
org.jacoco:jacoco-maven-plugin
```

Common Gradle plugin:

```gradle
jacoco
```

## Maven Commands

If JaCoCo is bound to the Maven lifecycle:

```bash
mvn test
```

If JaCoCo is configured but report is not bound:

```bash
mvn test jacoco:report
```

If the project has modules:

```bash
mvn -pl <module> test
mvn -pl <module> test jacoco:report
```

Typical report paths:

```text
target/site/jacoco/index.html
target/site/jacoco/jacoco.xml
target/site/jacoco/jacoco.csv
target/jacoco.exec
```

## Gradle Commands

Typical command:

```bash
./gradlew test jacocoTestReport
```

For multi-project builds:

```bash
./gradlew :<subproject>:test :<subproject>:jacocoTestReport
```

Typical report paths:

```text
build/reports/jacoco/test/html/index.html
build/reports/jacoco/test/jacocoTestReport.xml
build/reports/jacoco/test/jacocoTestReport.csv
build/jacoco/test.exec
```

## Parsing Reports Without A Browser

Prefer CSV or XML when available.

JaCoCo CSV columns commonly include:

```text
GROUP,PACKAGE,CLASS,INSTRUCTION_MISSED,INSTRUCTION_COVERED,
BRANCH_MISSED,BRANCH_COVERED,LINE_MISSED,LINE_COVERED,
COMPLEXITY_MISSED,COMPLEXITY_COVERED,METHOD_MISSED,METHOD_COVERED
```

Useful summary pattern:

```bash
awk -F, 'NR>1 {
  mi+=$4; ci+=$5; mb+=$6; cb+=$7; ml+=$8; cl+=$9; mm+=$12; cm+=$13
}
END {
  printf "Instruction: %.1f%%\n", ci*100/(ci+mi)
  printf "Branch: %.1f%%\n", cb*100/(cb+mb)
  printf "Line: %.1f%%\n", cl*100/(cl+ml)
  printf "Method: %.1f%%\n", cm*100/(cm+mm)
}' target/site/jacoco/jacoco.csv
```

Sort classes by missed lines:

```bash
awk -F, 'NR>1 {
  total=$8+$9
  if (total > 0) {
    printf "%4d missed  %6.1f line  %s.%s\n",
      $8, $9*100/total, $2, $3
  }
}' target/site/jacoco/jacoco.csv | sort -nr | head
```

## Interpretation

Java reports often include:

- DTOs and Lombok-generated methods.
- Framework bootstrap and configuration classes.
- Dependency injection wiring.
- Exception handlers and filters.

Do not chase generated accessors or framework wiring unless they contain validation, mapping, security, redaction, or public contract behavior.

High-signal Java gaps often include:

- Controllers/handlers with response contracts.
- Services with domain decisions.
- Repositories/stores with persistence and migration.
- Security filters, auth services, and credential handling.
- Resource lifecycle code such as pools, clients, handles, or classloaders.
- Exception translation and API error responses.

## Common Pitfalls

- `mvn test jacoco:report` may generate the report twice if the report goal is already bound to the lifecycle.
- Multi-module projects may need aggregate reports.
- Branch coverage can be low due to generated builders, null checks, or framework branches.
- Mock-heavy tests can execute code while failing to assert real behavior.
- Surefire/Failsafe split may require separate unit and integration coverage handling.
