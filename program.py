class Program():
  """ For each QC program registered with NYS Department of Education, collect information about the
      program scraped from the DoE website.
      Some programs appear more than once, so a class list of programs instances prevents duplicate
      entries.
  """
  headings = ['Program Code',
              'Title',
              'Awards',
              'HEGIS',
              'Unit Code',
              'TAP', 'APTS', 'VVTA',
              'Other Institution']

  # The programs dict is indexed by program_code. Needed to handle cases where the first query
  # produces multiple records for a single program.
  programs = {}

  def __init__(self, program_code):
    """ New program code: save program and unit code info.
    """

    if program_code not in self.programs.keys():
      self.programs[program_code] = self
      self.program_code = program_code
      self.institution = 'Unknown'
      self.unit_code = 'Unknown'
      self.awards = ''
      self.title = 'Unknown'
      self.hegis = 'Unknown'
      self.first_registration_date = 'Unknown'
      self.last_registration_date = 'Unknown'
      self.tap = 'Unknown'
      self.apts = 'Unknown'
      self.vvta = 'Unknown'
      self.certificate_license = ''
      self.accreditation = ''
      self.other_institution = ''

    else:
      pass  # details will be filled in from the details page

  def values(self, columns=None):
    """ Given a list of column headings, return the corresponding values.
        Could be used to generate a row of a spreadsheet.
    """
    if columns is None:
      columns = self.headings
    attributes = [h.lower().replace(' ', '_') for h in columns]

    return[getattr(self, col) for col in attributes]

  def __str__(self):
    return (self.__repr__().replace('program.Program object', 'NYS Registered Program')
            + f' {self.program_code:05}: {self.title} ({" ".join(self.awards)})')
