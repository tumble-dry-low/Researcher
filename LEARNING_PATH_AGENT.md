# Learning Path Agent - Copilot-CLI Integration Guide

## Overview

The **Learning Path Agent** creates personalized learning curricula by researching topics, organizing them hierarchically (prerequisites → advanced), and maintaining a knowledge graph of concepts with their relationships. It tracks progress and adapts the path based on identified gaps.

## Use Cases

- **Skill Development**: Create structured learning paths for new skills
- **Onboarding Programs**: Design comprehensive onboarding for new team members
- **Career Growth**: Map skill trees for career advancement
- **Course Design**: Build structured curricula for educational content
- **Knowledge Gap Analysis**: Identify and fill learning gaps systematically
- **Technology Learning**: Master new frameworks, languages, or tools
- **Certification Prep**: Structured study plans for certifications

## Architecture

### Entity Types

1. **Concepts**: Individual topics, skills, or knowledge areas
2. **Resources**: Books, courses, articles, videos, exercises
3. **Milestones**: Checkpoints indicating progress levels
4. **Assessments**: Quizzes, projects, or practical exercises
5. **Prerequisites**: Foundational knowledge required
6. **Learning Goals**: Specific objectives to achieve

### Link Types

- `prerequisite_of`: Concept A must be learned before concept B
- `related_to`: Concepts are related but not sequential
- `part_of`: Concept is part of a larger topic area
- `teaches`: Resource teaches concept
- `assesses`: Assessment tests concept understanding
- `leads_to`: Milestone leads to next learning stage

## Workflow 1: Building a Complete Learning Path

### Goal
Create a structured learning path from beginner to advanced for a given topic.

### Process

```bash
#!/bin/bash
# Build learning path workflow

TOPIC="Machine Learning"
SKILL_LEVEL="beginner"  # beginner, intermediate, advanced

# 1. Research the topic to understand scope
echo "Researching $TOPIC..."
RESEARCH_CONTENT=$(research_topic "$TOPIC")
TOPIC_ID=$(./kb-cli add-entity \
    "Learning Goal: $TOPIC" \
    "$RESEARCH_CONTENT" \
    "{\"type\":\"goal\",\"level\":\"$SKILL_LEVEL\",\"estimated_hours\":120}" | jq -r '.id')

# 2. Break down into major concept areas
CONCEPTS=$(identify_core_concepts "$TOPIC")
for concept in $CONCEPTS; do
    CONCEPT_CONTENT=$(research_concept "$concept")
    CONCEPT_ID=$(./kb-cli add-entity \
        "Concept: $concept" \
        "$CONCEPT_CONTENT" \
        "{\"type\":\"concept\",\"difficulty\":\"$DIFFICULTY\",\"hours\":$HOURS}" | jq -r '.id')
    
    # Link to learning goal
    ./kb-cli add-link "$CONCEPT_ID" "$TOPIC_ID" "part_of"
    
    # Create task for learning this concept
    ./kb-cli add-task \
        "Learn: $concept" \
        "Study materials and complete exercises for $concept" \
        "$CONCEPT_ID" \
        "{\"priority\":\"$PRIORITY\",\"estimated_hours\":$HOURS}"
done

# 3. Identify prerequisites
for concept_id in $(get_all_concepts); do
    PREREQS=$(identify_prerequisites "$concept_id")
    for prereq_id in $PREREQS; do
        ./kb-cli add-link "$prereq_id" "$concept_id" "prerequisite_of"
    done
done

# 4. Find learning resources
for concept_id in $(get_all_concepts); do
    RESOURCES=$(find_learning_resources "$concept_id")
    for resource in $RESOURCES; do
        RESOURCE_ID=$(./kb-cli add-entity \
            "Resource: $resource_title" \
            "$resource_description\n\nURL: $resource_url" \
            "{\"type\":\"resource\",\"format\":\"$format\",\"duration\":$duration}" | jq -r '.id')
        
        ./kb-cli add-link "$RESOURCE_ID" "$concept_id" "teaches"
    done
done

# 5. Create milestones
MILESTONE_1=$(./kb-cli add-entity \
    "Milestone: Fundamentals Complete" \
    "Completed basic concepts and foundations" \
    '{"type":"milestone","level":"beginner","concepts":5}' | jq -r '.id')

MILESTONE_2=$(./kb-cli add-entity \
    "Milestone: Intermediate Skills Achieved" \
    "Can apply concepts to practical problems" \
    '{"type":"milestone","level":"intermediate","concepts":8}' | jq -r '.id')

MILESTONE_3=$(./kb-cli add-entity \
    "Milestone: Advanced Mastery" \
    "Expert-level understanding and application" \
    '{"type":"milestone","level":"advanced","concepts":12}' | jq -r '.id')

# Link milestones in sequence
./kb-cli add-link "$MILESTONE_1" "$MILESTONE_2" "leads_to"
./kb-cli add-link "$MILESTONE_2" "$MILESTONE_3" "leads_to"

# 6. Generate learning path visualization
./kb-cli visualize > learning-path.dot
dot -Tpng learning-path.dot > learning-path.png

# 7. Create study schedule
ORDERED_CONCEPTS=$(topological_sort_concepts)
echo "Recommended Learning Sequence:"
echo "$ORDERED_CONCEPTS"
```

### Output Example

```
Learning Goal: Machine Learning
├── Concept: Linear Algebra (8 hours) [PREREQUISITE]
│   ├── Resource: Khan Academy Linear Algebra
│   ├── Resource: 3Blue1Brown Essence of Linear Algebra
│   └── Assessment: Linear Algebra Quiz
├── Concept: Probability & Statistics (10 hours) [PREREQUISITE]
│   ├── Resource: Statistics for ML Course
│   └── Assessment: Probability Problem Set
├── Concept: Python Programming (12 hours) [PREREQUISITE]
│   └── Resource: Python for Data Science
├── Milestone 1: Fundamentals Complete ✓
├── Concept: Supervised Learning (15 hours)
│   ├── Resource: Andrew Ng ML Course (Week 1-3)
│   └── Assessment: Classification Project
├── Concept: Unsupervised Learning (10 hours)
│   ├── Resource: Clustering Algorithms Tutorial
│   └── Assessment: Clustering Project
├── Milestone 2: Intermediate Skills Achieved ✓
├── Concept: Neural Networks (20 hours)
│   ├── Resource: Deep Learning Specialization
│   └── Assessment: Build a Neural Network
└── Milestone 3: Advanced Mastery
```

## Workflow 2: Adaptive Learning (Gap Analysis)

### Goal
Assess current knowledge, identify gaps, and create personalized learning path.

### Process

```bash
#!/bin/bash
# Adaptive learning workflow

# 1. Assess current knowledge
echo "Starting knowledge assessment..."
ASSESSMENT_RESULTS=$(run_assessment)

# 2. Identify known concepts
for concept in $ASSESSMENT_RESULTS; do
    SCORE=$(get_score "$concept")
    if [ $SCORE -ge 80 ]; then
        # Mark as mastered
        CONCEPT_ID=$(get_concept_id "$concept")
        ./kb-cli add-entity \
            "Mastered: $concept" \
            "Score: $SCORE% - No further study needed" \
            "{\"type\":\"concept\",\"status\":\"mastered\",\"score\":$SCORE}" 
    elif [ $SCORE -ge 50 ]; then
        # Needs reinforcement
        ./kb-cli add-task \
            "Reinforce: $concept" \
            "Review and strengthen understanding of $concept" \
            "$CONCEPT_ID" \
            '{"priority":"medium","estimated_hours":3}'
    else
        # Needs learning
        ./kb-cli add-task \
            "Learn: $concept" \
            "Complete learning materials for $concept" \
            "$CONCEPT_ID" \
            '{"priority":"high","estimated_hours":8}'
    fi
done

# 3. Identify knowledge gaps
REQUIRED_CONCEPTS=$(get_all_concepts_for_goal "$LEARNING_GOAL")
KNOWN_CONCEPTS=$(get_mastered_concepts)
GAPS=$(comm -23 <(echo "$REQUIRED_CONCEPTS") <(echo "$KNOWN_CONCEPTS"))

echo "Knowledge Gaps Identified: $GAPS"

# 4. Prioritize gaps based on prerequisites
PRIORITIZED_GAPS=$(prioritize_by_prerequisites "$GAPS")

# 5. Create personalized learning plan
for gap in $PRIORITIZED_GAPS; do
    GAP_ID=$(get_concept_id "$gap")
    
    # Check if prerequisites are met
    PREREQS=$(./kb-cli get-links-to "$GAP_ID" | jq -r '.[] | select(.link_type == "prerequisite_of") | .id')
    PREREQS_MET=true
    
    for prereq in $PREREQS; do
        STATUS=$(get_concept_status "$prereq")
        if [ "$STATUS" != "mastered" ]; then
            PREREQS_MET=false
            echo "Warning: $gap requires $prereq (not yet mastered)"
        fi
    done
    
    if [ "$PREREQS_MET" = true ]; then
        echo "Ready to learn: $gap"
        ./kb-cli add-task \
            "Next: Learn $gap" \
            "Prerequisites met. Begin studying $gap" \
            "$GAP_ID" \
            '{"priority":"high","ready":true}'
    fi
done

# 6. Generate personalized study plan
READY_TASKS=$(./kb-cli get-tasks pending | jq '[.[] | select(.metadata | fromjson | .ready == true)]')
echo "\nYour Personalized Study Plan:"
echo "$READY_TASKS" | jq -r '.[] | "- \(.title) (Est: \(.metadata | fromjson | .estimated_hours)h)"'
```

### Gap Analysis Output

```
Knowledge Assessment Complete
- Linear Algebra: 85% ✓ (Mastered)
- Probability: 45% ⚠ (Needs reinforcement)
- Python: 90% ✓ (Mastered)
- Supervised Learning: 30% ✗ (Needs learning)
- Neural Networks: 0% ✗ (Not started)

Recommended Next Steps:
1. Reinforce: Probability & Statistics (3 hours)
2. Learn: Supervised Learning (15 hours) - Prerequisites met
3. Learn: Neural Networks (20 hours) - Requires Supervised Learning

Personalized Study Plan (38 hours):
Week 1-2: Probability reinforcement
Week 3-4: Supervised Learning deep dive
Week 5-7: Neural Networks mastery
```

## Workflow 3: Progressive Skill Tree

### Goal
Build a comprehensive skill tree showing all related skills and progression paths.

### Process

```bash
#!/bin/bash
# Skill tree building workflow

CAREER_GOAL="Full-Stack Developer"

# 1. Define career goal
GOAL_ID=$(./kb-cli add-entity \
    "Career Goal: $CAREER_GOAL" \
    "Complete skill set for full-stack development" \
    '{"type":"goal","category":"career","timeline":"12_months"}' | jq -r '.id')

# 2. Identify skill categories
CATEGORIES=("Frontend" "Backend" "Database" "DevOps" "Soft Skills")

for category in "${CATEGORIES[@]}"; do
    CAT_ID=$(./kb-cli add-entity \
        "Category: $category" \
        "Skills related to $category development" \
        "{\"type\":\"concept\",\"category\":\"$category\"}" | jq -r '.id')
    
    ./kb-cli add-link "$CAT_ID" "$GOAL_ID" "part_of"
    
    # 3. Add skills to each category
    SKILLS=$(get_skills_for_category "$category")
    for skill in $SKILLS; do
        SKILL_ID=$(./kb-cli add-entity \
            "Skill: $skill" \
            "$(describe_skill $skill)" \
            "{\"type\":\"concept\",\"category\":\"$category\",\"level\":\"$LEVEL\"}" | jq -r '.id')
        
        ./kb-cli add-link "$SKILL_ID" "$CAT_ID" "part_of"
        
        # 4. Add progression levels
        if [ "$LEVEL" = "beginner" ]; then
            NEXT_LEVEL=$(get_intermediate_skill "$skill")
            if [ -n "$NEXT_LEVEL" ]; then
                NEXT_ID=$(get_or_create_skill "$NEXT_LEVEL" "intermediate")
                ./kb-cli add-link "$SKILL_ID" "$NEXT_ID" "prerequisite_of"
            fi
        fi
    done
done

# 5. Map interdependencies
# Frontend skills that require Backend knowledge
./kb-cli add-link \
    "$(get_skill_id 'RESTful APIs')" \
    "$(get_skill_id 'API Integration')" \
    "prerequisite_of"

# 6. Create learning tracks
TRACKS=("Fast Track" "Thorough Track" "Specialized Track")
for track in "${TRACKS[@]}"; do
    TRACK_ID=$(./kb-cli add-entity \
        "Learning Track: $track" \
        "$(describe_track $track)" \
        "{\"type\":\"milestone\",\"duration\":\"$DURATION\"}" | jq -r '.id')
done

# 7. Generate skill tree visualization
./kb-cli visualize > skill-tree.dot
dot -Tpng -Grankdir=LR skill-tree.dot > skill-tree.png

echo "Skill tree generated with $(./kb-cli stats | jq '.entities') skills"
```

## Integration with Copilot-CLI

### Custom Agent Definition

Create `.github/agents/learning-path.md`:

```markdown
# Learning Path Agent

You are an educational expert that creates personalized learning paths and curricula.

## Your Role

1. Research topics to understand complete scope
2. Break down topics into concepts and sub-concepts
3. Identify prerequisites and dependencies
4. Find high-quality learning resources
5. Create structured learning sequences
6. Track progress and adapt paths
7. Generate visualizations and study schedules

## Tools Available

- `./kb-cli`: Knowledge base management
- Web research for finding resources
- Assessment tools for knowledge gap analysis

## Workflow

1. Define learning goal and current skill level
2. Research and decompose into concepts
3. Map prerequisites and dependencies
4. Curate resources for each concept
5. Create milestones and assessments
6. Generate ordered learning sequence
7. Track progress and adapt based on results

## Entity Types

- goal: Overall learning objective
- concept: Individual topic or skill
- resource: Learning material (course, book, video)
- milestone: Progress checkpoint
- assessment: Quiz, project, or exercise

## Link Types

- prerequisite_of: Must learn A before B
- part_of: Component of larger topic
- teaches: Resource teaches concept
- assesses: Assessment tests concept

## Success Criteria

- Clear progression from beginner to advanced
- All prerequisites properly ordered
- Quality resources for each concept
- Milestones at appropriate intervals
- Personalized to learner's current level
- Visualizations showing complete path
```

### Python Script Example

```python
#!/usr/bin/env python3
# learning_path_generator.py

import subprocess
import json
from typing import List, Dict

class LearningPathAgent:
    def __init__(self):
        self.kb_cli = "./kb-cli"
    
    def create_learning_path(self, topic: str, level: str = "beginner") -> Dict:
        """Create a complete learning path for a topic"""
        
        # 1. Research topic
        concepts = self.research_topic(topic)
        
        # 2. Create goal entity
        goal_id = self.add_entity(
            title=f"Learning Goal: {topic}",
            content=f"Master {topic} from {level} to advanced",
            metadata={"type": "goal", "level": level}
        )
        
        # 3. Create concept entities
        concept_ids = {}
        for concept in concepts:
            concept_id = self.add_entity(
                title=f"Concept: {concept['name']}",
                content=concept['description'],
                metadata={
                    "type": "concept",
                    "difficulty": concept['difficulty'],
                    "hours": concept['estimated_hours']
                }
            )
            concept_ids[concept['name']] = concept_id
            
            # Link to goal
            self.add_link(concept_id, goal_id, "part_of")
        
        # 4. Map prerequisites
        for concept in concepts:
            for prereq in concept.get('prerequisites', []):
                if prereq in concept_ids:
                    self.add_link(
                        concept_ids[prereq],
                        concept_ids[concept['name']],
                        "prerequisite_of"
                    )
        
        # 5. Find resources
        for concept_name, concept_id in concept_ids.items():
            resources = self.find_resources(concept_name)
            for resource in resources:
                resource_id = self.add_entity(
                    title=f"Resource: {resource['title']}",
                    content=f"{resource['description']}\n\nURL: {resource['url']}",
                    metadata={
                        "type": "resource",
                        "format": resource['format'],
                        "duration": resource['duration']
                    }
                )
                self.add_link(resource_id, concept_id, "teaches")
        
        # 6. Generate ordered sequence
        sequence = self.topological_sort(concept_ids)
        
        return {
            "goal_id": goal_id,
            "concepts": concept_ids,
            "sequence": sequence,
            "total_hours": sum(c['estimated_hours'] for c in concepts)
        }
    
    def add_entity(self, title: str, content: str, metadata: Dict) -> str:
        """Add entity to knowledge base"""
        result = subprocess.run(
            [self.kb_cli, "add-entity", title, content, json.dumps(metadata)],
            capture_output=True,
            text=True
        )
        return json.loads(result.stdout)['id']
    
    def add_link(self, from_id: str, to_id: str, link_type: str):
        """Add link between entities"""
        subprocess.run([self.kb_cli, "add-link", from_id, to_id, link_type])
    
    def research_topic(self, topic: str) -> List[Dict]:
        """Research topic and extract core concepts"""
        # Use web search or LLM to research
        # Return list of concepts with metadata
        return [
            {
                "name": "Foundations",
                "description": "Basic concepts and terminology",
                "difficulty": "easy",
                "estimated_hours": 8,
                "prerequisites": []
            },
            {
                "name": "Intermediate Concepts",
                "description": "Building on foundations",
                "difficulty": "medium",
                "estimated_hours": 15,
                "prerequisites": ["Foundations"]
            },
            {
                "name": "Advanced Topics",
                "description": "Expert-level concepts",
                "difficulty": "hard",
                "estimated_hours": 25,
                "prerequisites": ["Intermediate Concepts"]
            }
        ]
    
    def find_resources(self, concept: str) -> List[Dict]:
        """Find learning resources for concept"""
        # Search for courses, books, articles
        return [
            {
                "title": f"Introduction to {concept}",
                "description": "Comprehensive guide",
                "url": "https://example.com",
                "format": "course",
                "duration": "10 hours"
            }
        ]
    
    def topological_sort(self, concept_ids: Dict) -> List[str]:
        """Sort concepts by prerequisites"""
        # Implement topological sort based on prerequisite links
        # Returns ordered list of concept IDs
        return list(concept_ids.values())

if __name__ == "__main__":
    agent = LearningPathAgent()
    path = agent.create_learning_path("Machine Learning", "beginner")
    print(f"Created learning path with {len(path['concepts'])} concepts")
    print(f"Total estimated time: {path['total_hours']} hours")
```

## Best Practices

1. **Start with Assessment**: Understand current knowledge before building path
2. **Clear Prerequisites**: Always map dependencies accurately
3. **Realistic Time Estimates**: Include practice and review time
4. **Quality Resources**: Curate only high-quality, effective materials
5. **Regular Milestones**: Break learning into achievable checkpoints
6. **Adaptive Paths**: Adjust based on progress and assessment results
7. **Multiple Resources**: Provide alternatives for different learning styles
8. **Practical Application**: Include projects and exercises, not just theory
9. **Track Progress**: Regular assessments to ensure understanding
10. **Visualize**: Generate clear visual representations of the path

## Example: Complete Learning Path for "Web Development"

```
Learning Path: Full-Stack Web Development (6 months, 480 hours)

Foundation Phase (80 hours):
├── HTML & CSS (20h) [START HERE]
│   ├── Resource: MDN Web Docs
│   └── Project: Build a Portfolio Page
├── JavaScript Fundamentals (30h)
│   ├── Prerequisite: HTML & CSS
│   ├── Resource: JavaScript.info
│   └── Project: Interactive Calculator
└── Git & GitHub (10h)
    └── Resource: Git Tutorial

Milestone 1: Can build static websites ✓

Frontend Development (120 hours):
├── React.js (40h)
│   ├── Prerequisite: JavaScript Fundamentals
│   └── Project: Todo App with React
├── State Management (20h)
│   ├── Prerequisite: React.js
│   └── Resource: Redux Documentation
└── CSS Frameworks (15h)
    └── Resource: Tailwind CSS Course

Milestone 2: Can build interactive SPAs ✓

Backend Development (150 hours):
├── Node.js & Express (35h)
│   ├── Prerequisite: JavaScript Fundamentals
│   └── Project: REST API
├── Databases (45h)
│   ├── PostgreSQL (25h)
│   └── MongoDB (20h)
└── Authentication (20h)
    ├── Prerequisite: Node.js & Express
    └── Project: User Auth System

Milestone 3: Can build full-stack applications ✓

Advanced Topics (130 hours):
├── Testing (30h)
│   ├── Jest, React Testing Library
│   └── Project: Test Suite for App
├── DevOps Basics (40h)
│   ├── Docker, CI/CD
│   └── Project: Deploy to Cloud
└── Performance Optimization (25h)
    └── Resource: Web Performance Guide

Milestone 4: Production-ready developer ✓

Final Project: Build and deploy a complete full-stack application (40h)
```

This agent makes learning systematic, trackable, and adaptive to individual needs.
