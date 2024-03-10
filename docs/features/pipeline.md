# {octicon}`workflow;1.5em;sd-mr-1` Pipeline Management

## Pipeline Configuration

Define and manage pipelines for installation, generation, building, and publishing phases with ease.

```{code-block} yaml
pipeline:
  - install:
    - step: RunScoop
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: Build
```

One can **extend** the pipeline with custom steps. The pipeline is executed in the order defined in the configuration file.

```{code-block} yaml
:emphasize-lines: 9-10
pipeline:
  - install:
    - step: RunScoop
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: Build
  - publish:
    - step: Artifactory
```

Pipeline steps can be **replaced** with custom steps.

```{code-block} yaml
:emphasize-lines: 8
pipeline:
  - install:
    - step: RunScoop
  - gen:
    - step: FeatureModel
  - build:
    - step: Configure
    - step: MyNewBuild
  - publish:
    - step: Artifactory
```

## Pipeline Execution

**Execution order**

All the steps in the pipeline are executed in the order defined in the configuration file.

**Execution context**

The execution context is passed to each step in the pipeline. The context contains the configuration, the environment, and the state of the pipeline.
Every step can modify the context to register new information or to modify the state of the pipeline.

**Dependency management**

Every step can define its dependencies. The pipeline executor will only run a step only if its dependencies have been changed or one of its outputs is missing.

**Single step execution**

It is possible to execute a single step in the pipeline. This is useful for debugging or for testing a single step.

For more details check the `run` command.

```{code-block} bash
yanga run --help
```
