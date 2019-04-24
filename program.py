class Program:
  """ For each QC program registered with NYS Department of Education, collect information about the
      program scraped from the DoE website.
      Some programs appear more than once, so a class list of programs instances prevents duplicate
      entries.
  """
  headings = ['Program Code',
              'Title',
              'Award',
              'HEGIS',
              'Unit Code',
              'TAP', 'APTS', 'VVTA',
              'Other Institution']

  # The programs dict is indexed by program_code. There is only one instance of this class per
  # program code.
  programs = {}

  def __new__(self, program_code):
    """ Return unique object for this program_code; create it first if necessary.
    """
    if program_code not in Program.programs.keys():
      Program.programs[program_code] = super().__new__(self)
    return Program.programs[program_code]

  def __init__(self, program_code):
    self.program_code = program_code
    self.institution = 'Unknown'
    self.unit_code = 'Unknown'
    self.__awards = []
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

  @property
  def award(self):
    return ' '.join(sorted(self.__awards))

  @award.setter
  def award(self, val):
    if val not in self.__awards:
      self.__awards.append(val)

  def values(self, columns=None):
    """ Given a list of column headings, return the corresponding values.
        Could be used to generate a row of a spreadsheet.
    """
    if columns is None:
      columns = self.headings
    attributes = [h.lower().replace(' ', '_') for h in columns]
    # if 'awards' in attributes:
    #   attributes[attributes.index('awards')] = '__awards'
    return[getattr(self, col) for col in attributes]

  def __str__(self):
    return (self.__repr__().replace('program.Program object', 'NYS Registered Program')
            + f' {self.program_code}: “{self.title}” ({self.award})')
