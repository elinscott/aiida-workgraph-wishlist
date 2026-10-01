A pydantic ``input_model`` as the task contract
================================================

**PR** `node-graph #182 <https://github.com/scinode/node-graph/pull/182>`__ · **PR** `aiida-workgraph #814 <https://github.com/aiidateam/aiida-workgraph/pull/814>`__

So far the philosophy while writing aiida-koopmans against aiida-workgraph has been to make it work given functions annotated with ``TypedDict`` classes and bare ``@task`` and ``@task.graph`` wrappers. The motivating idea: if someone turns up with well-annotated code, converting it to a workgraph should be easy. This has not proven to be the case.

After some conversations with Edan, a pivot to quite a different design is under way: a task's input (and output) contract is a pydantic model, with a minimally annotated function body. Pydantic's validation is a lot richer and can trigger at the right moment.

.. code-block:: python

   class PhInputs(BaseModel):
       spin: SpinType = SpinType.NONE
       structure: str

       @field_validator("spin")
       @classmethod
       def _supported(cls, v):
           if v in (SpinType.NON_COLLINEAR, SpinType.SPIN_ORBIT):
               raise ValueError("ph.x has no electric-field perturbation for noncollinear magnetism")
           return v


   @task(input_model=PhInputs)
   def ph(spin, structure):
       ...


   class WorkflowInputs(BaseModel):
       spin: SpinType = SpinType.NONE
       structure: str


   @task.graph(input_model=WorkflowInputs)
   def eps(spin, structure):
       return ph(spin=spin, structure=structure).dielectric


   eps.build(spin=SpinType.NON_COLLINEAR, structure="si")
   # TaskInputValidationError: Task 'ph' got inputs PhInputs rejects:
   #   spin: Value error, ph.x has no electric-field perturbation for noncollinear magnetism

Note the failure at build time, not run time. Pydantic also has rich support for serialization and coercion that the ``TypedDict`` strategy cannot match, though this is yet to be exploited.

The two branches are works in progress: the code is mostly unreviewed and the PR descriptions are partly polished AI ramblings.
