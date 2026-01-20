"""
Insurance Claim Agent
Main agent logic using Anthropic API with tool use.
"""

import anthropic
import os
import json
from typing import Generator
from tools import TOOL_DEFINITIONS, execute_tool

# System prompt for the insurance claim agent
SYSTEM_PROMPT = """You are an expert insurance claims assistant for Apex Auto Assurance. Your role is to help policyholders file and manage their insurance claims efficiently and professionally.

## Your Responsibilities:
1. **Greet and Assist**: Welcome users warmly and ask how you can help them today
2. **Collect Information**: Gather all necessary details about the claim systematically
3. **Verify Policy**: Look up the client's policy using their policy number or name
4. **Analyze Coverage**: Determine if the claim is covered based on their policy tier
5. **Assess Risk**: Evaluate the claim for any risk factors
6. **Guide Next Steps**: Provide clear instructions on what the policyholder needs to do

## Conversation Guidelines:
- Be professional, empathetic, and helpful
- Ask one or two questions at a time to avoid overwhelming the user
- Always verify the policy number before discussing coverage specifics
- Extract and confirm key details (dates, amounts, descriptions)
- When information is missing, politely ask for it
- Explain coverage decisions clearly, referencing specific policy terms

## Policy Tiers Overview:
- **Simple**: Basic liability coverage, fire & theft only, no collision
- **Advanced**: Comprehensive coverage with $1,000 collision deductible
- **Premium**: Full coverage with lowest deductibles and elite benefits

## Claim Process Flow:
1. Identify the policyholder
2. Understand the incident
3. Verify coverage applicability
4. Identify missing documentation
5. Provide investigation checklist
6. Explain next steps

## Important Notes:
- Claims must be reported within 24 hours of the incident
- Always check for general exclusions (ridesharing, racing, intentional acts)
- Premium members have access to 24/7 Concierge Claims line
- Be transparent about what is and isn't covered

Use your available tools to look up client information, analyze coverage, assess risk, and generate checklists. Always base your responses on actual policy data and client records."""


class InsuranceClaimAgent:
    """Insurance claim processing agent with tool use capabilities."""

    def __init__(self, api_key: str):
        """Initialize the agent with Anthropic API key."""
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        self.conversation_history = []
        self.claim_context = {}  # Store extracted claim information

    def reset_conversation(self):
        """Reset the conversation history and claim context."""
        self.conversation_history = []
        self.claim_context = {}

    def update_claim_context(self, key: str, value):
        """Update the claim context with new information."""
        self.claim_context[key] = value

    def get_claim_context(self) -> dict:
        """Get the current claim context."""
        return self.claim_context

    def _process_tool_calls(self, tool_calls: list) -> list:
        """Process tool calls and return results."""
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.name
            tool_input = tool_call.input

            # Execute the tool
            result = execute_tool(tool_name, tool_input)

            # Parse result to update context if needed
            try:
                result_data = json.loads(result)
                if tool_name == "lookup_client_by_policy" and result_data.get("found"):
                    self.claim_context["client"] = result_data
                elif tool_name == "lookup_client_by_name" and result_data.get("found") and not result_data.get("multiple_matches"):
                    self.claim_context["client"] = result_data
                elif tool_name == "extract_entities":
                    self.claim_context["extracted_entities"] = result_data
                elif tool_name == "analyze_coverage_applicability":
                    self.claim_context["coverage_analysis"] = result_data
                elif tool_name == "assess_risk":
                    self.claim_context["risk_assessment"] = result_data
            except json.JSONDecodeError:
                pass

            results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result
            })

        return results

    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.

        Args:
            user_message: The user's message

        Returns:
            The agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Make API call with tools
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=self.conversation_history
        )

        # Process the response
        assistant_message = {"role": "assistant", "content": response.content}
        self.conversation_history.append(assistant_message)

        # Handle tool use
        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_calls = [block for block in response.content if block.type == "tool_use"]

            # Process tools and get results
            tool_results = self._process_tool_calls(tool_calls)

            # Add tool results to history
            self.conversation_history.append({
                "role": "user",
                "content": tool_results
            })

            # Continue conversation
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.conversation_history
            )

            # Add new assistant message to history
            assistant_message = {"role": "assistant", "content": response.content}
            self.conversation_history.append(assistant_message)

        # Extract text response
        text_response = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_response += block.text

        return text_response

    def chat_stream(self, user_message: str) -> Generator[str, None, None]:
        """
        Send a message and stream the response.

        Args:
            user_message: The user's message

        Yields:
            Chunks of the agent's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        full_response = []
        current_tool_calls = []

        while True:
            # Make streaming API call
            with self.client.messages.stream(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOL_DEFINITIONS,
                messages=self.conversation_history
            ) as stream:
                current_text = ""
                for event in stream:
                    if hasattr(event, 'type'):
                        if event.type == 'content_block_delta':
                            if hasattr(event.delta, 'text'):
                                current_text += event.delta.text
                                yield event.delta.text

                # Get final message
                response = stream.get_final_message()

            # Add assistant message to history
            assistant_message = {"role": "assistant", "content": response.content}
            self.conversation_history.append(assistant_message)

            # Check if we need to handle tool use
            if response.stop_reason == "tool_use":
                # Extract tool calls
                tool_calls = [block for block in response.content if block.type == "tool_use"]

                # Process tools
                tool_results = self._process_tool_calls(tool_calls)

                # Add tool results to history
                self.conversation_history.append({
                    "role": "user",
                    "content": tool_results
                })

                # Signal that we're processing tools
                yield "\n\n*Processing...*\n\n"

            else:
                # No more tool calls, we're done
                break

    def get_conversation_summary(self) -> dict:
        """Get a summary of the current conversation and claim status."""
        return {
            "turn_count": len([m for m in self.conversation_history if m["role"] == "user"]),
            "claim_context": self.claim_context,
            "has_client": "client" in self.claim_context,
            "has_coverage_analysis": "coverage_analysis" in self.claim_context,
            "has_risk_assessment": "risk_assessment" in self.claim_context
        }
