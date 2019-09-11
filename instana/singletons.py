import sys
import opentracing

from .agent import Agent
from .autoprofile import start
from .tracer import InstanaTracer, InstanaRecorder


# The Instana Agent which carries along with it a Sensor that collects metrics.
agent = Agent()

# AutoProfile
auto_profile = start(
    agent_key = 'ec9f4e11633e795a9f8793bb961d1a3d020bc5a4',
    app_name = "BlueMonkey",
    debug=True)


span_recorder = InstanaRecorder()

# The global OpenTracing compatible tracer used internally by
# this package.
#
# Usage example:
#
# import instana
# instana.tracer.start_span(...)
#
tracer = InstanaTracer(recorder=span_recorder)

if sys.version_info >= (3,4):
    from opentracing.scope_managers.asyncio import AsyncioScopeManager
    async_tracer = InstanaTracer(scope_manager=AsyncioScopeManager(), recorder=span_recorder)


# Mock the tornado tracer until tornado is detected and instrumented first
tornado_tracer = tracer


def setup_tornado_tracer():
    global tornado_tracer
    from opentracing.scope_managers.tornado import TornadoScopeManager
    tornado_tracer = InstanaTracer(scope_manager=TornadoScopeManager(), recorder=span_recorder)


# Set ourselves as the tracer.
opentracing.tracer = tracer
