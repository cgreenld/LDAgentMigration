import os
from dotenv import load_dotenv
from ldclient import LDClient, Config
from ldclient.context import Context

# Load environment variables
load_dotenv()

def init_launchdarkly_polling():
    """Initialize LaunchDarkly SDK in polling mode"""

    
    # Configure LaunchDarkly client for polling mode
    config = Config(
        sdk_key="",
        # Polling mode settings
        poll_interval=30,      # Poll every 30 seconds
        stream=False,         # Disable streaming, use polling
        offline=False,        # Enable online mode
    )
    
    # Create client
    client = LDClient(config=config)
    
    # Wait for client to be ready (important for polling mode)
    print("Initializing LaunchDarkly client in polling mode...")
    client = LDClient(config=config)

    print("✅ LaunchDarkly client initialized successfully in polling mode")
    return client

def test_flag_evaluation():
    """Test flag evaluation with polling mode"""
    client = init_launchdarkly_polling()
    if not client:
        return
    
    # Create a context for flag evaluation
    context = Context.builder("test-user-123") \
        .kind("user") \
        .set("team", "platform") \
        .set("environment", "dev") \
        .build()
    
    # Test flag evaluation
    flag_key = "test-flag"  # Replace with your actual flag key
    default_value = False
    
    flag_value = client.variation(flag_key, context, default_value)
    print(f"Flag '{flag_key}' value: {flag_value}")
    
    # Test with a string flag
    string_flag_key = "test-string-flag"  # Replace with your actual flag
    string_default = "default-value"
    
    string_value = client.variation(string_flag_key, context, string_default)
    print(f"String flag '{string_flag_key}' value: {string_value}")
    
    # Get all flags for this context
    all_flags = client.all_flags_state(context)
    print(f"All flags state: {all_flags.to_json_dict()}")
    
    # Clean up
    client.close()
    print("LaunchDarkly client closed")

if __name__ == "__main__":
    print("Testing LaunchDarkly Python SDK in polling mode")
    print("=" * 50)
    
    test_flag_evaluation()
    
    print("\nPolling mode test completed!")
    print("Note: Changes in LaunchDarkly will be reflected within 30 seconds")