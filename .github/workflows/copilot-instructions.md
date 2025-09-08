# PiXie Agent - Copilot Instructions

## Project Overview

PiXie is an AI-powered conversational shopping assistant that helps customers find products through natural language interaction. The system uses internally accessible business information to understand, analyze complex product questions, and generate relevant recommendations.

## Core Concept

The system works as a digital sales assistant that:

- **Understands customer questions** in natural language, no matter how complex or vague they are formulated
- **Asks intelligent follow-up questions** to refine product specifications
- **Searches product catalogs** with both structured data and unstructured documentation
- **Provides personalized recommendations** with explanations and source references

## Technical Architecture

The system facilitates **natural product discovery** by guiding customers from vague intentions to specific product matches. It manages **complex conversations** that develop over multiple interactions, maintaining context and preferences.

The architecture supports **multi-source information retrieval**, making both structured product data and unstructured documentation searchable for accurate and complete answers.

## Business Value

PiXie automates the product advisory process by conducting human-like conversations while simultaneously having access to complete product catalogs and documentation. This results in better customer experience and increased conversion without the overhead of human customer service agents.

## Core Flows

Pixie supports several conversation patterns. A number of flows are illustrated with a simplified example dialogue. These flows summarize the most typical user interactions with Pixie and are representative of how the assistant behaves in practice.

### 1. Product found
A vague product request is gradually refined through follow-up questions until a concrete product list can be returned.

**Example**
- **Q:** I’m looking for a new printer  
- **A:** What is your budget for a printer? Less than €150, between €150–€300, more than €300, or no preference?  
- **Q:** Maximum €200  
- **A:** Which brand do you prefer? Brother, BenQ, HP, Kyocera, … or no preference?  
- **Q:** Brother  
- **A:** Which printing technology? Inkjet, laser, thermal inkjet, or no preference?  
- **Q:** Laser  
- **A:** Here are matching printers:  
  1. Brother XC 2570 – €199 – short description  
  2. Brother XT 3560 – €159 – short description  

### 2. Not relevant
When the question falls outside supported domains, Pixie gives a clear early exit.

**Example**
- **Q:** I’m looking for my mom  
- **A:** Sorry, I can’t help with that. I only have information about printers, laptops, smartphones, …

### 3. No results
Valid filters are applied but the query yields zero matches. Pixie responds gracefully and suggests alternatives.

**Example**
- **Q:** I want a Brother laser printer under €50  
- **A:** Unfortunately, no printers match your criteria. Please try again with a broader budget or contact support for assistance.

### 4. Too many results
When the query returns more than N results, Pixie offers refinement strategies or provides a manageable subset.

**Example**
- **Q:** I’m looking for a new printer  
- **A:** What is your budget?  
- **Q:** No preference  
- **A:** Which brand?  
- **Q:** No preference  
- **A:** Which printing technology?  
- **Q:** No preference  
- **A:** I found 152 printers. Would you like to see the top 5 sorted by price, or a random sample of 5?  
- **Q:** Sorted by price  
- **A:** Here are the top 5 printers:  
  1. Brother ZX 1570 – €69 – short description  
  2. HP Inkjet 234 – €79 – short description  
  3. Kyocera T70 – €99 – short description  
  4. Brother XT 3560 – €99 – short description  
  5. HP Inkjet 1234 – €109 – short description

## Vision and Long-term Goal

Pixie is designed to evolve into a modular and extensible system that can integrate with different data sources and reasoning engines. In the current version, adapters are mocked, but the long-term goal is to connect them as independent services through the Model Context Protocol (MCP).

The assistant should ultimately be able to:
- Seamlessly combine information from multiple adapters such as RAG, TabularRAG, and future specialized modules
- Reliably decide when more information is needed and phrase natural follow-up questions
- Provide transparent answers with traceable origins
- Function as a plug-and-play component that can be embedded in various user interfaces

## Development Approach

Pixie is intentionally built in incremental milestones.  
We start with a fully mocked prototype to validate flows and contracts, and gradually replace mocked components with real adapters and services.  
This step-by-step approach ensures that the system remains testable, understandable, and stable while steadily increasing functionality and realism.
