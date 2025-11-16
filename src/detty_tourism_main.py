# Detty-December Tourism Advisor Agent
# Main Orchestrator Agent - ADK Implementation
# Date: November 2025

import os
import json
import logging
from datetime import datetime
from typing import Any
from google.adk.agents import LlmAgent
from google.adk.tools import AgentTool, Tool
from google.genai.types import GenerateContentConfig, Tool as GeminiTool
from google import genai

# Configure logging for observability
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('tourism_agent.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Gemini client
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable is required")

client = genai.Client(api_key=API_KEY)

# ============================================================================
# MEMORY MANAGEMENT - Sessions & State
# ============================================================================

class TouristProfile:
    """Manages tourist session state and memory"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.created_at = datetime.now()
        self.preferences = {
            "budget": "moderate",  # budget, moderate, luxury
            "interests": [],       # ["culture", "nightlife", "shopping", etc]
            "duration": 0,         # days in Lagos
            "dietary_restrictions": [],
            "mobility_concerns": []
        }
        self.memory_bank = {
            "visited_places": [],
            "saved_restaurants": [],
            "bookings": [],
            "safety_alerts": [],
            "chat_history": []
        }
        self.session_state = "active"
        logger.info(f"Created tourist profile for {user_id}")
    
    def update_preferences(self, prefs: dict):
        """Update tourist preferences"""
        self.preferences.update(prefs)
        logger.info(f"Updated preferences for {self.user_id}: {prefs}")
    
    def save_to_memory(self, category: str, item: dict):
        """Save information to long-term memory"""
        if category in self.memory_bank:
            self.memory_bank[category].append({
                "data": item,
                "timestamp": datetime.now().isoformat()
            })
            logger.info(f"Saved {category} to memory for {self.user_id}")
    
    def to_dict(self) -> dict:
        """Serialize profile for context injection"""
        return {
            "user_id": self.user_id,
            "preferences": self.preferences,
            "recent_memory": {k: v[-5:] for k, v in self.memory_bank.items()}
        }


# Global session storage
sessions: dict[str, TouristProfile] = {}

def get_or_create_session(user_id: str) -> TouristProfile:
    """Get existing session or create new one"""
    if user_id not in sessions:
        sessions[user_id] = TouristProfile(user_id)
    return sessions[user_id]

# ============================================================================
# TOOL DEFINITIONS - Custom Tools for Tourism Advisor
# ============================================================================

def search_attractions(location: str, category: str, budget: str = "moderate") -> dict[str, Any]:
    """
    Search for tourist attractions in Lagos.
    
    Args:
        location: Area in Lagos (e.g., "Lekki", "VI", "Surulere", "Ikoyi")
        category: Type of attraction (e.g., "beach", "museum", "restaurant", "shopping", "nightlife")
        budget: Price range ("budget", "moderate", "luxury")
    
    Returns:
        Dictionary with list of attractions with names, descriptions, locations, ratings
    """
    logger.info(f"Tool call: search_attractions(location={location}, category={category}, budget={budget})")
    
    # Mock attraction database (in production: query real API)
    attractions_db = {
        ("Lekki", "beach", "budget"): [
            {"name": "Lekki Beach", "rating": 4.5, "price": "₦0", "hours": "6AM-6PM", "tip": "Go early to avoid crowds"},
            {"name": "Elegushi Beach", "rating": 4.3, "price": "₦500", "hours": "6AM-7PM"}
        ],
        ("VI", "shopping", "moderate"): [
            {"name": "Landmark Towers", "rating": 4.7, "price": "Various", "hours": "10AM-10PM"},
            {"name": "City Mall", "rating": 4.5, "price": "Various", "hours": "10AM-9PM"}
        ],
        ("Lekki", "restaurant", "moderate"): [
            {"name": "Craft", "rating": 4.6, "cuisine": "Continental", "price_range": "₦8000-₦20000"},
            {"name": "Cote Cuisine", "rating": 4.5, "cuisine": "African", "price_range": "₦7000-₦15000"}
        ],
        ("VI", "nightlife", "luxury"): [
            {"name": "Shisha Lounge", "rating": 4.4, "entry": "₦10000", "hours": "10PM-4AM"},
            {"name": "Club1 Lounge", "rating": 4.3, "entry": "₦15000", "hours": "9PM-5AM"}
        ]
    }
    
    key = (location, category, budget)
    results = attractions_db.get(key, [])
    
    return {
        "status": "success",
        "location": location,
        "category": category,
        "count": len(results),
        "attractions": results,
        "timestamp": datetime.now().isoformat()
    }


def check_safety_status(location: str, time_of_day: str = "day") -> dict[str, Any]:
    """
    Check safety information for Lagos locations.
    
    Args:
        location: Area in Lagos
        time_of_day: "day" or "night"
    
    Returns:
        Safety score, alerts, recommendations, emergency contacts
    """
    logger.info(f"Tool call: check_safety_status(location={location}, time_of_day={time_of_day})")
    
    safety_db = {
        "Lekki": {"day": 8, "night": 6, "alerts": [], "tip": "Generally safe, avoid isolated areas at night"},
        "VI": {"day": 9, "night": 8, "alerts": [], "tip": "Safest area, good security presence"},
        "Surulere": {"day": 6, "night": 4, "alerts": ["Avoid late night walks"], "tip": "Use registered taxis"},
        "Ikoyi": {"day": 8, "night": 7, "alerts": [], "tip": "Safe with standard precautions"}
    }
    
    safety_info = safety_db.get(location, {"day": 5, "night": 3, "alerts": ["Check latest info"], "tip": "Exercise caution"})
    score = safety_info[time_of_day]
    
    return {
        "location": location,
        "time_of_day": time_of_day,
        "safety_score": score,  # 1-10 scale
        "status": "safe" if score >= 7 else "caution" if score >= 5 else "avoid",
        "alerts": safety_info["alerts"],
        "recommendation": safety_info["tip"],
        "emergency_contacts": {
            "police": "999",
            "ambulance": "112",
            "tourism_hotline": "+234 700 000 0000"
        }
    }


def search_hotels(location: str, budget: str, nights: int, checkin_date: str) -> dict[str, Any]:
    """
    Search for hotel accommodations in Lagos.
    
    Args:
        location: Area preference (Lekki, VI, Surulere, etc)
        budget: "budget" (₦15K-30K), "moderate" (₦30K-80K), "luxury" (80K+)
        nights: Number of nights
        checkin_date: Check-in date (YYYY-MM-DD)
    
    Returns:
        List of hotels with prices, ratings, amenities
    """
    logger.info(f"Tool call: search_hotels(location={location}, budget={budget}, nights={nights})")
    
    hotels_db = {
        ("Lekki", "moderate"): [
            {"name": "Lekki Palm Hotel", "price_per_night": "₦45000", "rating": 4.6, "amenities": ["WiFi", "Pool", "Restaurant"], "booking_url": "mock://booking1"},
            {"name": "Radisson Blu", "price_per_night": "₦65000", "rating": 4.8, "amenities": ["WiFi", "Pool", "Gym", "Restaurant"]}
        ],
        ("VI", "luxury"): [
            {"name": "Eko Hotels", "price_per_night": "₦120000", "rating": 4.9, "amenities": ["WiFi", "Pool", "Gym", "Spa", "Restaurant"]},
            {"name": "Intercontinental", "price_per_night": "₦150000", "rating": 4.9, "amenities": ["WiFi", "Pool", "Gym", "Spa", "Fine Dining"]}
        ]
    }
    
    key = (location, budget)
    hotels = hotels_db.get(key, [])
    total_cost = int(hotels[0]["price_per_night"].replace("₦", "").replace(",", "")) * nights if hotels else 0
    
    return {
        "status": "success",
        "location": location,
        "checkin_date": checkin_date,
        "nights": nights,
        "hotel_count": len(hotels),
        "hotels": hotels,
        "estimated_total_cost": f"₦{total_cost:,}",
        "booking_note": "Prices subject to availability"
    }


def get_local_tips(category: str) -> dict[str, Any]:
    """
    Get insider tips for visiting Lagos during Detty-December.
    
    Args:
        category: "transport", "food", "culture", "safety", "events"
    
    Returns:
        List of practical tips and recommendations
    """
    logger.info(f"Tool call: get_local_tips(category={category})")
    
    tips = {
        "transport": [
            "Use Uber or Bolt instead of street taxis - safer and tracked",
            "Traffic is worst 7-9AM and 4-7PM - plan accordingly",
            "Danfo (minibus) is cheap but crowded - good for adventurous travelers"
        ],
        "food": [
            "Jollof rice competitions happen in December - try different spots",
            "Suya (grilled meat) is best at night on street corners",
            "Visit local markets (Lekki, Balogun) for authentic Lagos food"
        ],
        "culture": [
            "December festivals: Taste of Lagos, Lagos Street Festival",
            "Visit museums: Nike Centre, Lekki Conservation Centre",
            "Catch live music at Afrobeats venues - Lagos is music capital"
        ],
        "safety": [
            "Don't walk alone at night - use registered transport",
            "Keep valuables in hotel safe, carry minimal cash",
            "Register with your embassy before arrival",
            "Have travel insurance with medical coverage"
        ],
        "events": [
            "Detty-December starts Dec 1 - street parties every weekend",
            "Beach cleanups and community events throughout month",
            "Shopping festivals with discounts in Lekki and VI"
        ]
    }
    
    return {
        "category": category,
        "tips": tips.get(category, []),
        "last_updated": "2025-11-16",
        "source": "Local Lagos Tourism Guide"
    }


def make_booking_reminder(location: str, activity: str, date: str, time: str, tourist_id: str) -> dict[str, Any]:
    """
    Set booking reminders for activities and events.
    
    Args:
        location: Where the activity is
        activity: What to book (hotel, restaurant, tour, event)
        date: Date of activity (YYYY-MM-DD)
        time: Time of activity (HH:MM)
        tourist_id: Tourist session ID
    
    Returns:
        Confirmation of reminder set
    """
    logger.info(f"Tool call: make_booking_reminder(activity={activity}, date={date}, time={time})")
    
    # Save to tourist's memory
    session = get_or_create_session(tourist_id)
    session.save_to_memory("bookings", {
        "activity": activity,
        "location": location,
        "date": date,
        "time": time,
        "status": "reminder_set"
    })
    
    return {
        "status": "success",
        "reminder_id": f"REM-{tourist_id}-{date}-{activity}",
        "activity": activity,
        "location": location,
        "scheduled_date": date,
        "scheduled_time": time,
        "message": f"Reminder set for {activity} at {location} on {date} at {time}",
        "notification_method": "SMS + Email (simulated)"
    }

# ============================================================================
# SUB-AGENTS - Specialized agents for different domains
# ============================================================================

# Initialize sub-agents
tourism_advisor_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="TourismAdvisor",
    description="Expert on Lagos tourism attractions, restaurants, shopping, culture, and entertainment",
    instructions="""You are a knowledgeable Lagos tourism guide specializing in Detty-December experiences.
    
Your role:
- Recommend attractions based on tourist interests and budget
- Suggest restaurants and food experiences
- Provide cultural insights about Lagos
- Help plan itineraries
- Use search_attractions tool to find specific recommendations
- Use get_local_tips to share insider knowledge

Always ask about preferences first before recommending."""
)

safety_guide_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="SafetyGuide",
    description="Provides safety information, security tips, and emergency guidance for Lagos",
    instructions="""You are a safety and security expert for Lagos tourism.

Your role:
- Assess safety of locations and neighborhoods
- Provide security best practices for travelers
- Check current safety status using check_safety_status tool
- Give practical safety advice based on time of day and location
- Provide emergency contacts and resources
- Never minimize real safety concerns - always prioritize tourist safety

Format safety info clearly and actionably."""
)

booking_assistant_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="BookingAssistant",
    description="Handles hotel bookings, reservations, and activity bookings",
    instructions="""You are a professional booking coordinator for Lagos experiences.

Your role:
- Search for hotels matching tourist needs
- Help make reservation decisions
- Set booking reminders and confirmations
- Use search_hotels tool to find accommodations
- Use make_booking_reminder to confirm bookings
- Provide clear booking details and cancellation policies
- Track all bookings in tourist profile

Always confirm preferences and dates before searching."""
)

# ============================================================================
# MAIN ORCHESTRATOR AGENT
# ============================================================================

def build_orchestrator_context(tourist_id: str) -> str:
    """Build context with tourist profile and session state"""
    session = get_or_create_session(tourist_id)
    profile = session.to_dict()
    return f"""
Current Tourist Profile:
- User ID: {profile['user_id']}
- Preferences: {json.dumps(profile['preferences'], indent=2)}
- Recent Activity: {json.dumps(profile['recent_memory'], indent=2)}

You have access to specialized sub-agents:
1. TourismAdvisor - recommendations for attractions and experiences
2. SafetyGuide - safety information and security guidance
3. BookingAssistant - hotel and activity bookings

Always consider the tourist's profile when delegating tasks."""


def create_orchestrator_agent(tourist_id: str) -> LlmAgent:
    """Create main orchestrator with sub-agents and tools"""
    
    # Wrap sub-agents as tools
    tourism_tool = AgentTool(agent=tourism_advisor_agent)
    safety_tool = AgentTool(agent=safety_guide_agent)
    booking_tool = AgentTool(agent=booking_assistant_agent)
    
    # Create main orchestrator
    orchestrator = LlmAgent(
        model="gemini-2.5-flash",
        name="DettyDecemberAdvisor",
        description="Main orchestrator for Detty-December Lagos tourism experiences",
        instructions=f"""You are the main Detty-December Tourism Advisor for Lagos.

Your mission: Help tourists arriving in Lagos this December have the best experience safely and affordably.

Tourist Context:
{build_orchestrator_context(tourist_id)}

Available capabilities:
1. Tourism Advisor Agent - for attraction and restaurant recommendations
2. Safety Guide Agent - for security and safety information
3. Booking Assistant Agent - for hotel and reservation management

Your coordination logic:
- Always greet new tourists warmly with Detty-December spirit
- Assess their needs (interests, budget, duration, concerns)
- Delegate specialized tasks to appropriate sub-agents
- Consolidate responses into actionable itineraries
- Prioritize safety alongside enjoyment
- Save all recommendations to their session memory

Response format:
1. Welcome/Assessment (if first interaction)
2. Key Recommendations (from relevant sub-agents)
3. Next Steps / Call-to-Action
4. Emergency Info (if needed)

Remember: You're their local guide, concierge, and safety advocate.""",
        tools=[
            tourism_tool,
            safety_tool,
            booking_tool
        ]
    )
    
    # Log agent creation
    logger.info(f"Created orchestrator agent for tourist {tourist_id}")
    logger.info(f"Orchestrator has {len(orchestrator.tools)} sub-agents attached")
    
    return orchestrator


# ============================================================================
# CONVERSATION LOOP
# ============================================================================

def run_tourism_advisor():
    """Main conversation loop for the Tourism Advisor"""
    
    print("\n" + "="*70)
    print("🌴  DETTY-DECEMBER LAGOS TOURISM ADVISOR  🌴")
    print("="*70)
    print("Welcome! This AI agent helps tourists explore Lagos safely this December.")
    print("Type 'quit' to exit, 'clear' to start new session.\n")
    
    # Get tourist ID
    tourist_id = input("Enter your name or tourist ID: ").strip() or f"Tourist-{datetime.now().timestamp()}"
    logger.info(f"New conversation started with tourist: {tourist_id}")
    
    # Create orchestrator for this tourist
    orchestrator = create_orchestrator_agent(tourist_id)
    
    # Save tourist profile
    session = get_or_create_session(tourist_id)
    
    print(f"\n✅ Welcome, {tourist_id}! I'm your Detty-December guide for Lagos.")
    print("Tell me about your trip - interests, budget, concerns, and I'll help plan it!\n")
    
    conversation_history = []
    
    while True:
        user_input = input(f"{tourist_id}: ").strip()
        
        if not user_input:
            continue
        
        if user_input.lower() == 'quit':
            logger.info(f"Tourist {tourist_id} ended session")
            print(f"\n🙏 Thank you for using Detty-December Advisor! Enjoy Lagos! Stay safe!")
            break
        
        if user_input.lower() == 'clear':
            if tourist_id in sessions:
                del sessions[tourist_id]
            orchestrator = create_orchestrator_agent(tourist_id)
            session = get_or_create_session(tourist_id)
            print("✨ Session cleared. Let's start fresh!\n")
            continue
        
        # Log user input
        logger.info(f"User input from {tourist_id}: {user_input}")
        conversation_history.append({"role": "user", "content": user_input})
        
        try:
            # Call orchestrator
            response = orchestrator.generate_content(
                contents=user_input,
                config=GenerateContentConfig(
                    temperature=0.7,
                    response_modalities=["TEXT"],
                )
            )
            
            # Extract response
            agent_response = response.candidates[0].content.parts[0].text
            conversation_history.append({"role": "agent", "content": agent_response})
            
            # Save to memory
            session.memory_bank["chat_history"].extend([
                {"role": "user", "content": user_input},
                {"role": "agent", "content": agent_response}
            ])
            
            print(f"\n🤖 Tourism Advisor:\n{agent_response}\n")
            logger.info(f"Agent response sent to {tourist_id}")
            
        except Exception as e:
            error_msg = f"⚠️ Error: {str(e)}\nPlease try again or rephrase your request."
            print(f"\n{error_msg}\n")
            logger.error(f"Error processing request from {tourist_id}: {str(e)}", exc_info=True)
    
    # Log final session
    logger.info(f"Final session data for {tourist_id}: {session.to_dict()}")


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    logger.info("Starting Detty-December Tourism Advisor Agent")
    logger.info(f"Timestamp: {datetime.now()}")
    
    try:
        run_tourism_advisor()
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        print("\n\nAgent stopped. Goodbye!")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"Fatal error: {str(e)}")
        raise
