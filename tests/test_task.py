import pytest

from notion_task_runner.task import Task

"""
100% coverage is nice :)
"""

class ConcreteTask(Task):
  def run(self):
    return "test-result"


def test_concrete_task_run_executes():
  task = ConcreteTask()
  result = task.run()
  assert result == "test-result"

def test_abstract_task_instantiation_fails():
  with pytest.raises(TypeError):
    Task()