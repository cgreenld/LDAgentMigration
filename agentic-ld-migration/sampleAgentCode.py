from launchdarkly_sdk import LdClient
from launchdarkly_sdk.ai import LdAiClient, Context

ld_client = LdClient(sdk_key="YOUR_SDK_KEY")
ai_client = LdAiClient(ld_client)

context = Context.builder("INC12345") \
                 .kind("incident_report") \
                 .set("region", "Dallas") \
                 .set("affected_customers", 2400) \
                 .set("description", "Core routers in Dallas experiencing packet loss and outages since 8:45 AM.") \
                 .build()

fallback = {"enabled": False}
agent_config = ai_client.agent(
    key="network-incident-triage-agent",
    context=context,
    default_value=fallback
)

if agent_config.enabled:
    print("Agent goal:", agent_config.instructions)
else:
    print("Agent disabled, fallback triggered.")
