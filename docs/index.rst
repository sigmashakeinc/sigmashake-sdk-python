SigmaShake Python SDK
=====================

Python SDK for the SigmaShake platform API — agent-first, async-native, type-safe.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api

Quick Start
-----------

.. code-block:: python

   from sigmashake import SigmaShake

   client = SigmaShake(api_key="sk-...")

   # Create an auth token
   token = client.auth.create_token(agent_id="agent-1", scopes=["read", "write"])

   # Scan an operation with Shield
   result = client.shield.scan(
       agent_id="agent-1",
       session_id="sess-1",
       operation={"name": "Bash", "input": {"command": "ls"}},
   )

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
