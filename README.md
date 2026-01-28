# Insurance Claim Agent

An AI-powered insurance claims assistant for Apex Auto Assurance. This chatbot helps policyholders file and manage their insurance claims through a conversational interface with support for image uploads to assess vehicle damage.

## Features

- **Conversational Claims Processing**: Natural language interface for filing insurance claims
- **Client Lookup**: Search clients by policy number or name
- **Coverage Analysis**: Automatic determination of claim coverage based on policy tier
- **Risk Assessment**: Evaluate claims for potential risk factors
- **Image Analysis**: Upload and analyze photos of vehicle damage
- **Investigation Checklists**: Generate documentation requirements for claims
- **Real-time Streaming**: Responses stream in real-time for better user experience

## Tech Stack

- **Frontend**: Streamlit
- **AI Model**: Anthropic Claude (claude-sonnet-4-20250514)
- **Language**: Python 3.12
- **Image Processing**: Pillow (PIL)

## Project Structure

```
insuranceClaimAgent/
├── src/
│   ├── app.py          # Streamlit web application
│   ├── agent.py        # Insurance claim agent with Anthropic API
│   └── tools.py        # Tool definitions for claim processing
├── docs/
│   ├── Clients.csv     # Client database
│   └── Insurance Policy.pdf  # Policy documentation
├── environment.yml     # Conda environment configuration
└── README.md
```

## Installation

### Prerequisites

- Conda or Miniconda
- Anthropic API key

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd insuranceClaimAgent
   ```

2. Create the conda environment:
   ```bash
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```bash
   conda activate insurance-claim-env
   ```

4. Set up your Anthropic API key:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```

## Usage

Start the Streamlit application:

```bash
streamlit run src/app.py
```

The application will open in your browser at `http://localhost:8501`.

### Filing a Claim

1. Start a conversation by describing your claim
2. Provide your policy number or name when asked
3. Upload images of vehicle damage (optional)
4. Follow the agent's guidance to complete your claim

## Policy Tiers

The system supports three policy tiers:

| Tier | Coverage | Collision Deductible |
|------|----------|---------------------|
| **Simple** | Basic liability, fire & theft only | No collision coverage |
| **Advanced** | Comprehensive coverage | $1,000 |
| **Premium** | Full coverage with elite benefits | Lowest deductibles |

## Available Tools

The agent has access to the following tools:

- `lookup_client_by_policy` - Find client by policy number
- `lookup_client_by_name` - Find client by name
- `get_coverage_details` - Get detailed coverage information for a tier
- `analyze_coverage_applicability` - Determine if a claim is covered
- `extract_entities` - Extract relevant information from claim descriptions
- `assess_risk` - Evaluate risk factors in a claim
- `generate_investigation_checklist` - Create documentation requirements

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Yes |

### Image Upload

- Supported formats: JPG, JPEG, PNG
- Images are automatically compressed to optimize API usage
- Multiple images can be attached per message

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Structure

- **agent.py**: Contains the `InsuranceClaimAgent` class that handles conversation flow, tool execution, and image processing
- **tools.py**: Defines all available tools and their implementations
- **app.py**: Streamlit UI with chat interface and file upload handling


