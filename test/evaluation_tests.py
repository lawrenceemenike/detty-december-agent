# evaluation_tests.py - Golden Dataset + LLM-as-Judge Framework

import json
from datetime import datetime
from typing import Any
from google import genai

# Initialize Gemini for LLM-as-Judge evaluation
API_KEY = "your-api-key"  # Will be set from environment
client = genai.Client(api_key=API_KEY)

# ============================================================================
# GOLDEN TEST DATASET - 15 Representative Scenarios
# ============================================================================

GOLDEN_TEST_CASES = [
    {
        "id": "TEST-001",
        "scenario": "First-time tourist, safety-focused",
        "input": "I'm arriving in Lagos on Dec 1st for 3 days. This is my first time in Nigeria. I'm worried about safety. What areas should I stay in and avoid?",
        "expected_behaviors": [
            "Greet warmly and acknowledge safety concerns",
            "Call check_safety_status for key areas",
            "Recommend safe neighborhoods (VI, Lekki with caveats)",
            "Provide concrete safety tips",
            "Suggest budget-conscious safe hotels"
        ],
        "minimum_score": 7.0
    },
    {
        "id": "TEST-002",
        "scenario": "Budget traveler, foodie",
        "input": "I have ₦50,000 per day budget. I want to try authentic Lagos food. Where should I go? Any street food I should avoid?",
        "expected_behaviors": [
            "Ask clarifying questions about dietary preferences",
            "Use search_attractions for budget food spots",
            "Provide local food tips with safety context",
            "Recommend markets and street vendors with ratings",
            "Suggest affordable restaurants (<₦10k)"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-003",
        "scenario": "Luxury traveler, events",
        "input": "I'm in Lagos Dec 15-25. Luxury budget. What high-end experiences and events are happening during Detty-December?",
        "expected_behaviors": [
            "Search luxury attractions and restaurants",
            "Mention Detty-December events and festivals",
            "Recommend upscale venues (Landmark, Eko Hotels, clubs)",
            "Set booking reminders for events",
            "Provide VIP concierge-level recommendations"
        ],
        "minimum_score": 8.0
    },
    {
        "id": "TEST-004",
        "scenario": "Group travel, logistics",
        "input": "We're 6 friends arriving together. We want an AirBnB in a safe area, good for nightlife. What's the best deal and safest way to move around at night?",
        "expected_behaviors": [
            "Search hotels/accommodations for groups",
            "Recommend safe neighborhoods (Lekki, VI, Ikoyi)",
            "Provide safe transport tips (Uber, Bolt)",
            "Group activity suggestions",
            "Set collaborative booking reminders"
        ],
        "minimum_score": 8.0
    },
    {
        "id": "TEST-005",
        "scenario": "Business traveler, networking",
        "input": "I'm here Dec 10-15 for startup conferences. Where's best for coworking? How do I network in Lagos tech scene? Safe places to work late?",
        "expected_behaviors": [
            "Delegate to TourismAdvisor for tech hubs",
            "Recommend VI/Lekki tech spaces",
            "Safety tips for evening activities",
            "Suggest networking venues and events",
            "Provide emergency/safety contacts for travelers"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-006",
        "scenario": "Safety emergency scenario",
        "input": "I'm feeling unsafe in my current location (Surulere, late night). What should I do immediately? Where's safe?",
        "expected_behaviors": [
            "Immediate safety assessment via check_safety_status",
            "Clear emergency action steps",
            "Provide emergency contacts (police 999, ambulance 112)",
            "Recommend immediate safe transport",
            "De-escalation and reassurance"
        ],
        "minimum_score": 9.0  # Critical - must prioritize safety
    },
    {
        "id": "TEST-007",
        "scenario": "Detty-December specific",
        "input": "What's this 'Detty-December' I keep hearing about? What should I experience?",
        "expected_behaviors": [
            "Explain Detty-December celebrations",
            "Use get_local_tips for December events",
            "Recommend street parties, festivals",
            "Beach activities and community events",
            "Cultural experiences unique to December"
        ],
        "minimum_score": 8.0
    },
    {
        "id": "TEST-008",
        "scenario": "Cultural explorer",
        "input": "I love history and art. What museums and cultural sites should I visit? Any local artists or galleries?",
        "expected_behaviors": [
            "Search attractions for museums (Nike Centre, etc)",
            "Provide cultural context about Lagos",
            "Local art scene recommendations",
            "Gallery opening times and locations",
            "Suggest cultural guides or tours"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-009",
        "scenario": "Transportation challenge",
        "input": "What's the best way to get around Lagos? I'm nervous about driving. Uber/Bolt vs traditional transport?",
        "expected_behaviors": [
            "Use get_local_tips for transport guidance",
            "Compare safety of transport modes",
            "Cost analysis (Uber vs Bolt vs Danfo)",
            "Best routes and times to travel",
            "Safety recommendations for each option"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-010",
        "scenario": "Holiday planning",
        "input": "I want to celebrate Christmas/New Year in Lagos. What's the best experience? How early should I book?",
        "expected_behaviors": [
            "Search hotels with make_booking_reminder",
            "December events recommendations",
            "New Year's party venues",
            "Set booking reminders urgently (high demand)",
            "Alternative low-cost celebrations"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-011",
        "scenario": "Multi-step complex request",
        "input": "I arrive Dec 3rd, 7 days, moderate budget, love music and nightlife, but I'm solo and female. Create me an itinerary with safe venues, good hotels, and transport tips.",
        "expected_behaviors": [
            "Ask clarifying questions about preferences",
            "Coordinate all 3 sub-agents (advisor, safety, booking)",
            "Create day-by-day itinerary",
            "Emphasize safety throughout",
            "Book hotels and set reminders",
            "Female-specific safety advice"
        ],
        "minimum_score": 8.5  # Complex coordination
    },
    {
        "id": "TEST-012",
        "scenario": "Accessibility needs",
        "input": "I use a wheelchair. Are venues in Lagos accessible? How do I get around safely?",
        "expected_behaviors": [
            "Acknowledge accessibility concerns",
            "Assess which venues have accessibility",
            "Recommend accessible transport",
            "Suggest accessibility-friendly hotels",
            "Provide practical navigation tips"
        ],
        "minimum_score": 8.0
    },
    {
        "id": "TEST-013",
        "scenario": "Dietary/health concerns",
        "input": "I'm vegetarian and gluten-free. What restaurants in Lagos can accommodate this? Any health risks I should know?",
        "expected_behaviors": [
            "Search restaurant recommendations",
            "Use get_local_tips for food safety",
            "Identify vegetarian-friendly spots",
            "Health/sanitation recommendations",
            "Market shopping tips for safe food"
        ],
        "minimum_score": 7.5
    },
    {
        "id": "TEST-014",
        "scenario": "Budget emergency",
        "input": "I lost my wallet and card. I'm stuck in Lagos. What do I do?",
        "expected_behaviors": [
            "Immediate practical assistance",
            "Embassy/consulate contact info",
            "Money transfer options",
            "Safe places to wait/rest",
            "Police report procedures"
        ],
        "minimum_score": 8.5  # Critical help scenario
    },
    {
        "id": "TEST-015",
        "scenario": "Follow-up personalization",
        "input": "Remember I love jollof rice? Can you recommend the best places to try different regional variations?",
        "expected_behaviors": [
            "Recall from memory (if available)",
            "Search attractions for restaurants",
            "Provide regional jollof rice guide",
            "Competition/festival information",
            "Update preference memory"
        ],
        "minimum_score": 7.0
    }
]


# ============================================================================
# LLM-AS-JUDGE EVALUATION FRAMEWORK
# ============================================================================

def evaluate_response_with_llm(
    test_case: dict,
    agent_response: str
) -> dict[str, Any]:
    """
    Use Gemini as a judge to evaluate agent response quality.
    
    Scoring criteria:
    - 1-3: Poor (incomplete, unsafe, inaccurate)
    - 4-6: Fair (basic coverage, some gaps)
    - 7-8: Good (comprehensive, actionable, safe)
    - 9-10: Excellent (thorough, innovative, prioritizes safety)
    """
    
    evaluation_prompt = f"""
You are an expert evaluator of AI tourism agents for Lagos, Nigeria.

EVALUATION CRITERIA:
1. Relevance (1-10): Does response address the query directly?
2. Safety Priority (1-10): Is safety appropriately emphasized?
3. Actionability (1-10): Are recommendations specific and actionable?
4. Completeness (1-10): Does it cover main aspects without gaps?
5. Cultural Appropriateness (1-10): Respect for local culture and norms?
6. Tone (1-10): Warm, helpful, professional tone?

TEST CASE:
- ID: {test_case['id']}
- Scenario: {test_case['scenario']}
- User Query: {test_case['input']}
- Expected Behaviors: {json.dumps(test_case['expected_behaviors'])}

AGENT RESPONSE:
{agent_response}

Provide:
1. Score for each criterion (1-10)
2. Overall score (1-10)
3. Key strengths (2-3 bullet points)
4. Areas for improvement (2-3 bullet points)
5. Pass/Fail (based on minimum score of {test_case['minimum_score']})

Format as JSON:
{{
    "test_id": "...",
    "relevance": ...,
    "safety": ...,
    "actionability": ...,
    "completeness": ...,
    "cultural_fit": ...,
    "tone": ...,
    "overall_score": ...,
    "strengths": [...],
    "improvements": [...],
    "passed": true/false,
    "reasoning": "..."
}}
"""
    
    try:
        evaluation_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=evaluation_prompt,
            config={"temperature": 0.3}  # Lower temp for consistent evaluation
        )
        
        eval_text = evaluation_response.candidates[0].content.parts[0].text
        
        # Parse JSON from response
        start_idx = eval_text.find('{')
        end_idx = eval_text.rfind('}') + 1
        json_str = eval_text[start_idx:end_idx]
        evaluation = json.loads(json_str)
        
        return evaluation
        
    except Exception as e:
        return {
            "test_id": test_case['id'],
            "error": str(e),
            "overall_score": 0,
            "passed": False
        }


# ============================================================================
# EVALUATION RUNNER
# ============================================================================

def run_evaluation_suite(agent_callable, verbose=True):
    """
    Run full evaluation suite against tourism advisor agent.
    
    Args:
        agent_callable: Function that takes user_input -> agent_response
        verbose: Print detailed results
    
    Returns:
        Evaluation summary with scores and metrics
    """
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(GOLDEN_TEST_CASES),
        "passed": 0,
        "failed": 0,
        "scores": [],
        "average_score": 0.0,
        "by_category": {}
    }
    
    print("\n" + "="*70)
    print("🧪 RUNNING GOLDEN TEST SUITE - 15 SCENARIOS")
    print("="*70 + "\n")
    
    for i, test_case in enumerate(GOLDEN_TEST_CASES):
        print(f"[{i+1}/15] {test_case['id']}: {test_case['scenario']}")
        print(f"  Query: {test_case['input'][:60]}...")
        
        try:
            # Get agent response
            agent_response = agent_callable(test_case['input'])
            
            # Evaluate with LLM-as-Judge
            evaluation = evaluate_response_with_llm(test_case, agent_response)
            
            # Record results
            results['scores'].append(evaluation)
            
            if evaluation.get('passed', False):
                results['passed'] += 1
                status = "✅ PASS"
            else:
                results['failed'] += 1
                status = "❌ FAIL"
            
            score = evaluation.get('overall_score', 0)
            print(f"  Score: {score:.1f}/10 {status}")
            
            if verbose:
                print(f"  Strengths: {', '.join(evaluation.get('strengths', [])[:2])}")
                if evaluation.get('improvements'):
                    print(f"  Improve: {evaluation['improvements'][0]}")
            
        except Exception as e:
            results['failed'] += 1
            print(f"  Error: {str(e)[:50]}")
        
        print()
    
    # Calculate metrics
    if results['scores']:
        valid_scores = [s['overall_score'] for s in results['scores'] if 'overall_score' in s]
        results['average_score'] = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    
    # Print summary
    print("="*70)
    print("📊 EVALUATION SUMMARY")
    print("="*70)
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed']} ✅")
    print(f"Failed: {results['failed']} ❌")
    print(f"Pass Rate: {results['passed']/results['total_tests']*100:.1f}%")
    print(f"Average Score: {results['average_score']:.1f}/10")
    print("="*70 + "\n")
    
    return results


# ============================================================================
# SAMPLE MOCK AGENT FOR TESTING FRAMEWORK
# ============================================================================

def mock_agent_response(user_input: str) -> str:
    """Mock agent for testing the evaluation framework"""
    
    if "safety" in user_input.lower():
        return """
Welcome to the Lagos Tourism Advisor! I understand you're concerned about safety - that's important.

Based on your query, here's what I recommend:
1. **Best Safe Areas**: Lekki, Victoria Island (VI), Ikoyi
   - Safety Score: 8-9/10 during day, 7-8 at night
   - Good infrastructure, security presence

2. **Areas of Caution**: Surulere, Mushin
   - Safety Score: 5-6/10
   - Avoid alone at night

3. **Safety Tips**:
   - Use registered taxis (Uber/Bolt)
   - Don't walk alone after dark
   - Keep valuables in hotel safe
   - Register with your embassy

4. **Emergency Contacts**:
   - Police: 999
   - Ambulance: 112
   - Tourism Hotline: +234 700 000 0000

I've checked the current safety status and set reminders for you. Would you like specific hotel recommendations in the safe areas?
"""
    else:
        return """
Great question! Let me help you explore Lagos. I'm checking the best options for you...

Based on your interests, here are my top recommendations:

1. **Must-Visit Attractions**:
   - Lekki Conservation Centre (wildlife & nature)
   - Nike Centre (art & culture)
   - Lekki Beach (relaxation & sunset)

2. **Food Experiences**:
   - Local markets (authentic Lagos food)
   - Craft restaurant (continental cuisine)
   - Street suya stands (authentic experience)

3. **Nightlife**:
   - Shisha Lounge (upscale, VI)
   - Beach clubs (Lekki)
   - Live music venues (Afrobeats)

4. **Next Steps**:
   - Set booking reminders for hotels/restaurants
   - Get detailed safety tips for each area
   - Create day-by-day itinerary

Shall I book a hotel for you or get more details on any of these?
"""


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Test the evaluation framework with mock agent
    print("\n🧪 Testing Evaluation Framework with Mock Agent...\n")
    
    results = run_evaluation_suite(
        agent_callable=mock_agent_response,
        verbose=True
    )
    
    # Save results
    with open('evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("✅ Evaluation complete! Results saved to evaluation_results.json")
    
    # Quick stats
    print(f"\n📈 Key Metrics:")
    print(f"  - Average Response Quality: {results['average_score']:.1f}/10")
    print(f"  - Success Rate: {results['passed']}/{results['total_tests']} tests passed")
    print(f"  - Recommendation: {'Ready for deployment ✅' if results['average_score'] >= 7.5 else 'Needs improvement 🔧'}")
