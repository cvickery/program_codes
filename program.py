from recordclass import recordclass

items = ['institution',
         'title',
         'hegis',
         'first_registration_date',
         'last_registration_date',
         'tap', 'apts', 'vvta',
         'certificate_license',
         'accreditation']
award_info = recordclass('Award_Info', items)


class Program(object):
  """ For each QC program registered with NYS Department of Education, collect information about the
      program scraped from the DoE website.
      Some programs appear more than once, so a class list of programs instances prevents duplicate
      entries.
      2019-04-25: Re-conceptualize: a program has a dict of info about an award.The info is
      maintained as a recordclass so the values can be updated as new records are retrieved from
      nys. A recordclass is like a namedtuple, but the values are mutable. Problem is, it's still in
      beta ... but seems to be under active development.
  """

  headings = ['Institution',
              'Title',
              'Award',
              'HEGIS',
              'Certificate or License',
              'Accreditation',
              'First Registration Date',
              'Last Registration Date',
              'TAP', 'APTS', 'VVTA']

  # The (public) programs dict is indexed by program_code. There is only one instance of this class
  # per program code.
  programs = {}

  def __new__(self, program_code):
    """ Return unique object for this program_code; create it first if necessary.
    """
    if program_code not in Program.programs.keys():
      Program.programs[program_code] = super().__new__(self)
      Program.programs[program_code].awards = dict()
    return Program.programs[program_code]

  def __init__(self, program_code):
    self.program_code = program_code
    self.unit_code = 'Unknown'

  @property
  def award(self):
    return ' '.join(sorted(self.awards.keys()))

  @award.setter
  def award(self, award_str):
    if award_str not in self.awards.keys():
      self.awards[award_str] = award_info._make([None] * len(items))

  def values(self, award, headings=None):
    """ Given a list of column headings, yield the corresponding values for each award.
        Does not include program-wide values (program code and registration office’s unit code).
    """
    if headings is None:
      headings = self.headings
    fields = [h.lower().replace(' or ', '_').replace(' ', '_') for h in headings]
    return [self.awards[award][field] if field != 'award' else award for field in fields]

  def __str__(self):
    return (self.__repr__().replace('program.Program object', 'NYS Registered Program')
            + f' {self.program_code} {self.unit_code} {self.awards}')

