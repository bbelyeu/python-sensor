import sys
import opentracing

from .agent import Agent
from .autoprofile.agent import AutoProfileAgent
from .tracer import InstanaTracer, InstanaRecorder


# The Instana Agent which carries along with it a Sensor that collects metrics.
agent = Agent()

ap_agent = AutoProfileAgent(debug=True)
ap_agent.start()
ap_agent.enable()

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
