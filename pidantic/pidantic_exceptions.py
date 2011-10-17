
class PIDanticUsageException(Exception):

  def __init__(self, message):
      Exception.__init__(self, message)

class PIDanticStateException(Exception):

  def __init__(self, message):
      Exception.__init__(self, message)

class PIDanticExecutionException(Exception):

  def __init__(self, message):
      Exception.__init__(self, message)
