# AI-SPRINT API

Initial implementation of the AI-SPRINT API. 

Currently implemented functionalities:
- Creation of new AI-SPRINT applications from template (based on cookiecutter)
- AI-SPRINT annotations (security annotations must be added)
- Parsing of AI-SPRINT annotations (security annotations must be added)
- Creation of AI-SPRINT designs (only base design, partitioning tool must be added)
- Parsing of annotations for each design
- Generation of configuration files for each design given the provided annotations:
    - Currently only 'exec_time'-derived constraints for monitoring tool
- Some error checking:
    - DAG format
    - Annotations syntax. Implemented for:
        - component_name
        - exec_time
        - expected_throughput (to be revised)
        - partitionable_model (to be revised)
    - Annotations semantic. Implemented for:
        - exec_time

## Quick-Start
---

### Step1: Install Requirements (Python 3.8.10):
```
python3 -m pip install cookiecutter==2.1.1
```

### Step2: Install AI-SPRINT 
```
git clone https://gitlab.polimi.it/ai-sprint/ai-sprint-api.git
cd ai-sprint-api
python3 -m pip install . 
```

### Step3: Try --help 
```
aisprint --help
```

## Example1: Create new application
```
aisprint new-application --application_name NAME
```

## Example2: Parse annotations and create designs 
### example application in 'examples'
```
aisprint create-designs --application_dir ./NAME
```