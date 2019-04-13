class Program():
  """ For each QC program registered with NYS Department of Education, college information about the
      program scraped from the DoE website.
  """
  def __init__(self, program_code, title, hegis, unit_code, award):
    self.program_code = program_code
    self.title = title
    self.hegis = hegis
    self.unit_code = unit_code
    self.award = award
    self.tap = 'Unknown'
    self.apts = 'Unknown'
    self.vvta = 'Unknown'
    self.other_institution = 'Unknown'
    self.headings = ['Program Code',
                     'Title',
                     'HEGIS',
                     'Unit Code',
                     'Award',
                     'TAP', 'APTS', 'VVTA',
                     'Other Institution']

  def values(self, headings):
    """ Given a list of column headings, return the corresponding values.
        Used to generate a row of a csv output file.
    """
    if headings is None:
      headings = self.headings
    attributes = [h.lower().replace(' ', '_') for h in headings]
    return[getattr(self, col) for col in attributes]

  def __str__(self):
    return (self.__repr__().replace('program.Program object', 'NYS Registered Program')
            + f' {self.program_code:05}: {self.title} ({self.award})')
