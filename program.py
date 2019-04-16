class Program():
  """ For each QC program registered with NYS Department of Education, college information about the
      program scraped from the DoE website.
      Some programs appear more than once, with the effect of changing the registration date range;
      for these, the range is adjusted as new instances occur.
  """
  headings = ['Program Code',
              'Unit Code',
              'Title',
              'HEGIS',
              'TAP', 'APTS', 'VVTA',
              'Joint With']
  programs = {}

  def __init__(self, *args, **kwargs):
    """ Program(<program number>,
                institution=<institution name>,
                award=<award>,
                unit_code=OP|OCUE
                [, title=<program title>]
                [, hegis=<hegis code>]
                [, tap=<boolean>]
                [, apts=<boolean>]
                [, vvta=<boolean>]
    """
    # Required positional argument
    if len(args) != 1:
      raise TypeError(f'Expected one positional argument, but got {len(args)}')
    program_code = int(args[0])

    # Required keyword arguments
    unit_code = kwargs.get('unit_code', None)
    if unit_code is None:
      raise TypeError('Missing Unit Code')
    self.unit_code = unit_code
    institution = kwargs.get('institution', None)
    if institution is None:
      raise TypeError('Missing Institution')
    award = kwargs.get('award', None)
    if award is None:
      raise TypeError('Missing Award')

    # Optional keyword arguments
    title = kwargs.get('title', 'Unknown')
    hegis = kwargs.get('hegis', 'Unknown')

    if program_code not in self.programs.keys():
      self.programs[program_code] = self
      self.program_code = program_code
      self.institution_awards = [(fix_title(institution), award)]
      self.title = fix_title(title)
      self.hegis = hegis
      self.first_registration_date = 'Unknown'
      self.last_registration_date = 'Unknown'
      self.tap = 'Unknown'
      self.apts = 'Unknown'
      self.vvta = 'Unknown'

    else:
      # Use the values supplied to add new institution/award for the existing program.
      program = self.programs[program_code]
      if program.unit_code != unit_code:
        raise TypeError(
            f'Unit Code ({unit_code}) does not match previous value ({program.unit_code})')
      institution_award = (fix_title(institution), award)
      if institution_award not in self.institution_awards:
        self.institution_awards.append(institution_award)

  def values(self, columns=None):
    """ Given a list of column headings, return the corresponding values.
        Used to generate a row of a csv output file.
    """
    if columns is None:
      columns = self.headings
    self.joint_with = '; '.join(self.institutions)
    attributes = [h.lower().replace(' ', '_') for h in columns]
    return[getattr(self, col) for col in attributes]

  def __str__(self):
    return (self.__repr__().replace('program.Program object', 'NYS Registered Program')
            + f' {self.program_code:05}: {self.title} ({" ".join(self.awards)})')
