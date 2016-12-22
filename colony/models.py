"""
TODO
Validation scripts that check that the genotype of each mouse meshes with
the parents
Auto-determine needed action for each litter (and breeding cage?)
Auto-id litters
Slug the mouse name from the litter name and toe num?
"""


from __future__ import unicode_literals

from django.db import models
import datetime
from django.core import urlresolvers
from simple_history.models import HistoricalRecords
from django.utils import timezone
from django.contrib.auth.models import User
from autoslug import AutoSlugField

# Helper function to get a new cage nuber based on user
def get_series_number_from_user_name(user_name):
    """Returns the series number for this user.
    
    Their cages will be in the range 
        1000*series_number:1000*(series_number+1)
    
    Here we use the login name, rather than the name on the Person class.
    0 is returned if the user_name is not known.
    """
    if user_name == 'amanda':
        series_number = 9
    elif user_name == 'chris':
        series_number = 3
    elif user_name == 'Dan':
        series_number = 5
    elif user_name == 'georgia':
        series_number = 9
    elif user_name == 'kate':
        series_number = 1
    elif user_name == 'library':
        series_number = 10
    elif user_name == 'lab stock':
        series_number = 10
    else:
        series_number = 2
    return series_number

def get_person_name_from_user_name(user_name):
    """Return the person corresponding to the logged-in user"""
    if user_name == 'amanda':
        return 'Amanda'
    elif user_name == 'chris':
        return 'Chris'
    elif user_name == 'christina':
        return 'Christina'        
    elif user_name == 'Dan':
        return 'Dan'
    elif user_name == 'Drew':
        return 'Drew'
    elif user_name == 'georgia':
        return 'Georgia'
    elif user_name == 'jpatterson':
        return 'Jason'
    elif user_name == 'kate':
        return 'Kate'
    elif user_name == 'randy':
        return 'Randy'
    else:
        return None

def get_user_name_from_person_name(person_name):
    """Return the user name corresponding to the person name
    
    This is used to determine the input to get_series_number_from_user_name
    in the make_mating_cage form.
    
    person_name : Proprietor name
    
    Returns: user_name
        Suitable for get_series_number_from_user_name
    """
    if person_name == 'Amanda':
        return 'amanda'
    elif person_name == 'Chris':
        return 'chris'
    elif person_name == 'Christina':
        return 'christina'        
    elif person_name == 'Dan':
        return 'Dan'
    elif person_name == 'Drew':
        return 'Drew'
    elif person_name == 'Georgia':
        return 'georgia'
    elif person_name == 'Jason':
        return 'jpatterson'
    elif person_name == 'Kate':
        return 'kate'
    elif person_name == 'Randy':
        return 'randy'
    elif person_name == 'Library':
        return 'library'
    elif person_name == 'Lab Stock':
        return 'lab stock'        
    else:
        return None

def strip_alpha(cage_name):
    """Keep only digits from cage name
    
    Ignores any initial alpha characters
    Then takes digits until the next alpha character is reached
    Then returns the digits as an integer, or None if no match.
    """
    res = ''
    started_taking_digits = False
    for char in cage_name:
        if not started_taking_digits:
            if char in '0123456789':
                started_taking_digits = True
                res += char
            else:
                continue
        else:
            if char in '0123456789':
                res += char
            else:
                break
    
    if len(res) == 0:
        return None
    else:
        return int(res)

def generate_cage_name(user_name=None):
    """Returns the next cage name for this user.
    
    user_name : logged-in user's name
    
    Finds all existing cage names and chooses one number higher.
    Returns: the new cage name as a string
    """
    # Determine what cage series it is
    series_number = get_series_number_from_user_name(user_name)
    
    # Find all cage numbers in this series
    all_cage_names = Cage.objects.all().values_list('name', flat=True)
    my_cage_numbers = []
    for cage_name in all_cage_names:
        try:
            cage_num = int(cage_name)
        except (TypeError, ValueError):
            continue
        if (cage_num // 1000 == series_number):
            my_cage_numbers.append(cage_num)
    
    # This was a previous algorithm that failed after 9999
    #~ my_cages = Cage.objects.filter(name__startswith=str(series_number))
    #~ cage_names = list(my_cages.values_list('name', flat=True))
    #~ cage_numbers = map(strip_alpha, cage_names)
    #~ cage_numbers = filter(lambda num: num is not None, cage_numbers)
    
    # Generate a new cage number that is 1 higher
    if len(my_cage_numbers) == 0:
        target_cage = series_number * 1000 + 1
    else:
        target_cage = max(my_cage_numbers) + 1
    #~ target_cage_name = '%04d' % target_cage
    target_cage_name = str(target_cage)
    
    # Error check
    if not target_cage_name.startswith(str(series_number)):
        raise ValueError("cannot generate new cage name, series full?")
    if Cage.objects.filter(name=target_cage_name).count() > 0:
        raise ValueError("cannot generate new unique cage name")
    
    return target_cage_name

# This needs to be here for a weird migration
def get_tgeno():
    pass

# Create your models here.

class Person(models.Model):
    name = models.CharField(max_length=15, unique=True)    
    
    # track history with simple_history
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

def slug_target_genotype(litter):
    """Function to generate a target genotype slug from a cage
    
    The model itself calls this function via AutoSlugField.
    
    If the litter has already been weaned, or if its cage is defunct,
    then this returns 'NA'. That's because we typically only use this
    for filtering for active litters.
    
    To generate the slug, we first get the genotype of both parents. Then
    try to put the driver line first and the reporter second. If we
    can't identify which is which, return in alphabetical order.
    """
    if litter.breeding_cage.defunct:
        return 'NA'
    
    g1 = str(litter.father.genotype)
    g2 = str(litter.mother.genotype)
    drivers = ['cre']
    reporters = ['flex', 'halo', 'tdtomato', 'mcherry']
    for driver in drivers:
        if driver in g1.lower():
            return g1 + ' x ' + g2
        elif driver in g2.lower():
            return g2 + ' x ' + g1
    
    for reporter in reporters:
        if reporter in g2.lower():
            return g1 + ' x ' + g2
        elif reporter in g1.lower():
            return g2 + ' x ' + g1
    
    if g1 < g2:
        return g1 + ' x ' + g2
    else:
        return g2 + ' x ' + g1

def my_slugify(s):
    """Don't apply any prettification to the slug, such as removing +"""
    return s

def have_same_single_gene(mouse1, mouse2):
    """Returns True if mouse1 and mouse2 have the same single MouseGene
    
    This is mainly useful for detecting homozygosing crosses
    """
    if mouse1.mousegene_set.count() != 1:
        return False
    if mouse2.mousegene_set.count() != 1:
        return False
    
    mg1 = mouse1.mousegene_set.first()
    mg2 = mouse2.mousegene_set.first()
    
    if mg1.gene_name.id == mg2.gene_name.id:
        return True
    else:
        return False


class Cage(models.Model):
    """Model for a cage.

    """
    name = models.CharField(max_length=10, unique=True)    
    notes = models.CharField(max_length=100, blank=True, null=True)
    defunct = models.BooleanField(default=False)
    location = models.IntegerField(
        choices = (
            (0, '1710'),
            (1, '1702'),
            (2, 'Behavior'),
            ),
        default=0
        )
    
    # Needs to be made mandatory
    proprietor = models.ForeignKey('Person')
    
    # track history with simple_history
    history = HistoricalRecords()
    
    @property
    def cage_type(self):
        """Return the type of the cage
        
        The type is always "type_string (relevant_gene_string)"
        
        Here are the possible types:
        Breeding cages
        *   "pure stock": all mice are pure_breeder
            The relevant gene can be "mixed genotype", "WT", or "no genotype"
        *   "progeny": at least one mouse is impure
            The relevant gene can be "mixed genotype", "WT", "no genotype",
            or "gene1 x gene2" (where all mice have the same gene1, gene2, etc.)
        
        Non-breeding cages
        *   "outcross": at least one parent has wild_type=True
            The relevant gene is the other parent's new_genotype
        *   "incross": both parents have the same single gene
            The relevant gene is that gene
        *   "cross": anything else
            The relevant gene is "mother_new_genotype x father_new_genotype"
        
        TODO: return type_string, relevant_gene_l in a more standard way,
            always preferring gene not genotype, and making it amenable
            to filtering by gene
        """
        if not hasattr(self, 'litter') or self.litter.date_weaned is not None:
            # no breeding
            
            # If all mice are pure, we label it "pure stock"
            all_mice_pure = True
            
            # If all mice are wild-type, we label it "pure wild-type"
            all_mice_wildtype = True
            
            # Otherwise keep track of which mousegenes each mouse has
            relevant_mousegene_set = None
            mixed_mousegene_sets = False
            
            # Iterate over each mouse
            for mouse in self.mouse_set.all():
                # If any mouse is impure, the cage cannot be pure stock
                if not mouse.pure_breeder:
                    all_mice_pure = False
                
                # If any mouse is not wild_type, the cage can't be WT
                if not mouse.wild_type:
                    all_mice_wildtype = False
                
                # Set relevant_mousegene_set if it's the same for all mice
                this_mouse = list(mouse.mousegene_set.values_list(
                    'gene_name__name', flat=True))
                if relevant_mousegene_set is None:
                    relevant_mousegene_set = this_mouse
                elif this_mouse != relevant_mousegene_set:
                    mixed_mousegene_sets = True
            
            # Stringify relevant_mousegene_set
            if mixed_mousegene_sets:
                mousegene_s = 'mixed genotype'
            elif all_mice_wildtype:
                mousegene_s = 'WT'
            elif len(relevant_mousegene_set) == 0:
                mousegene_s = 'no genotype'
            else:
                mousegene_s = ' x '.join(relevant_mousegene_set)
            
            if all_mice_pure:
                return "pure stock (%s)" % mousegene_s
            else:
                return "progeny (%s)" % mousegene_s
        
        else:
            # yes breeding
            # determine whether it's a cross against WT or between two genotypes
            breed_type = 'none'
            if self.litter.mother.wild_type:
                # Outcross, mother WT
                breed_type = 'outcross'
                relevant_gene = self.litter.father.new_genotype
            elif self.litter.father.wild_type:
                # Outcross, father WT
                breed_type = 'outcross'
                relevant_gene = self.litter.mother.new_genotype
            elif have_same_single_gene(self.litter.father, self.litter.mother):
                breed_type = 'incross'
                relevant_gene = self.litter.mother.mousegene_set.first().gene_name.name
            else:
                # Cross
                breed_type = 'cross'
                relevant_gene = '%s x %s' % (
                    self.litter.father.new_genotype,
                    self.litter.mother.new_genotype,
                )
            
            return "%s (%s)" % (breed_type, relevant_gene)
    
    def notes_first_half(self, okay_line_length=25):
        """Return the first half of the notes. For CensusView display
        
        Deprecated since we started specifying CensusView column widths.
        """
        s = str(self.notes)
        if len(s) < okay_line_length or ' ' not in s:
            return s
        
        # Find all spaces
        spi = [i for i, letter in enumerate(s) if letter == ' ']
        dist_from_center = [abs(spii - len(s) / 2) for spii in spi]

        # Find the space closest to the middle of the string
        best_space_idx, min_dist_from_center = min(enumerate(
            dist_from_center), key=lambda x:x[1])
        split_idx = spi[best_space_idx]
        
        return s[:split_idx]
    
    def notes_second_half(self, okay_line_length=25):
        s = str(self.notes)
        if len(s) < okay_line_length or ' ' not in s:
            return ''
        
        # Find all spaces
        spi = [i for i, letter in enumerate(s) if letter == ' ']
        dist_from_center = [abs(spii - len(s) / 2) for spii in spi]

        # Find the space closest to the middle of the string
        best_space_idx, min_dist_from_center = min(enumerate(
            dist_from_center), key=lambda x:x[1])
        split_idx = spi[best_space_idx]
        
        return s[split_idx:]

    def get_special_request_message(self):
        res_l = []
        for sr in self.specialrequest_set.all():
            if sr.date_completed is None:
                res_l.append("<b>@%s: %s</b>" % (sr.requestee, sr.message))
            else:
                res_l.append("<strike>@%s: %s</strike>" % (sr.requestee, sr.message))
        return '<br>'.join(res_l)

    def n_mice(self):
        return len(self.mouse_set.all())
    
    def names(self):
        """Return list of all mice in this cage"""
        name_l = []
        for m in self.mouse_set.all():
            name_l.append(m.name)
        return ', '.join(name_l)
    
    def infos(self):
        """Return list of all mice in this cage with additional info on each"""
        # Get info from each contained mouse and prepend "pup" to pups
        info_l = []
        for mouse in self.mouse_set.order_by('name').all():
            m_info = mouse.info()
            if mouse.still_in_breeding_cage:
                m_info = 'pup ' + m_info
            info_l.append(m_info)
        
        return '<pre>' + '<br>'.join(info_l) + '</pre>'
    
    # I think this is to allow a user-readable column name in admin
    infos.allow_tags = True
    infos.short_description = "Mouse Info"

    def age(self):
        age = None
        for mouse in self.mouse_set.all():
            if age is None:
                age = mouse.age()
            elif age != mouse.age():
                return None
        return age
    
    def __str__(self):
        return self.name
    
    def auto_needs_message(self):
        srm = self.get_special_request_message()
        try:
            lanm = self.litter.auto_needs_message()
        except Litter.DoesNotExist:
            lanm = ''
        
        if srm != '' and lanm != '':
            return srm + '<br />' + lanm
        else:
            return srm + lanm
    auto_needs_message.allow_tags = True
    
    def target_genotype(self):
        if self.litter:
            return self.litter.target_genotype
        else:
            return 'NA'
    target_genotype.admin_order_field = 'litter__target_genotype'
    
    def change_link(self):
        """Get a link to the change page
        
        Probably doesn't belong in models.py
        """
        return urlresolvers.reverse("admin:colony_cage_change", args=[self.id])        
    
    @property
    def contains_mother_of_this_litter(self):
        """Returns True if the mother of this cage's litter is still present.
        
        This is True while she is raising the litter but becomes False
        after the pups are weaned (which technically means the mother was
        moved to a new cage).
        
        This is used to test whether we should display info about the
        "litter" in various views. Typically we don't really care about
        it as a "litter" after weaning, at least for the purposes of
        determining what the litter needs.
        
        Actually, a simpler way would just be to test if the litter
        has a wean date.
        """
        # Return False if litter doesn't exist
        try:
            self.litter
        except Litter.DoesNotExist:
            return False
        
        if self.litter:
            if self.litter.mother:
                if self.litter.mother.cage:
                    if self.litter.mother.cage == self:
                        # The mother exists and is still here
                        return True
                    else:
                        # The mother exists but is in another cage
                        return False
                else:
                    # No cage set for the mother
                    return False
            else:
                # no mother set, probably not possible
                return False
        else:
            # litter is None, this is probably impossible
            return False

class Genotype(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    # track history with simple_history
    history = HistoricalRecords()
    
    def __str__(self):
        return self.name

class Mouse(models.Model):
    """Model for a Mouse.
    
    Required fields
        name: unique. Should almost always be LITTERNUM-TOENUM
        sex: M, F, or ?
        genotype: foreign key to genotype
    
    Optional fields that are often set
        cage: cage object in which this mouse is physically located
        sack_date: date of death
        breeder: boolean, used mainly for filtering in MouseList to see
            whether we have enough breeders

    When mice are born and added to the tabular inline for the breeding
    cage, a Litter object is created and set to be the "litter" attribute
    on this mouse.

    "Override" fields. Typically these data are calculated by traversing
    to the mouse's Litter. Some mice were grandfathered into the db or
    were purchased and so no Litter object is available.
        manual_dob : date of birth
        manual_father
        manual_mother
    """
    # Required fields
    name = models.CharField(max_length=15, unique=True)
    sex = models.IntegerField(
        choices=(
            (0, 'M'),
            (1, 'F'),
            (2, '?'),
            )
        )
    genotype = models.ForeignKey(Genotype)
    
    # Whether this mouse is a pure breeder
    # This means that any offspring it has with WT mice will also be
    # pure breeders. We will mainly use this to identify maintenance
    # cages vs experimental cages. I can't think of a reason why
    # a pure breeder would have more than one MouseGene, but maybe it's
    # possible.
    pure_breeder = models.BooleanField(default=False)
    
    # Whether this mouse is a wild type. It should not have any MouseGene
    # in this case. May need to have another field for "strain".
    wild_type = models.BooleanField(default=False)
    
    # Optional fields that can be set by the user
    cage = models.ForeignKey(Cage, null=True, blank=True)
    sack_date = models.DateField('sac date', blank=True, null=True)
    breeder = models.BooleanField(default=False)
    user = models.ForeignKey(Person, null=True, blank=True)    
    notes = models.CharField(max_length=100, null=True, blank=True)    
    
    # These fields are normally calculated from Litter but can be overridden
    manual_dob = models.DateField('DOB override', blank=True, null=True)
    manual_father = models.ForeignKey('Mouse', 
        null=True, blank=True, related_name='mmf')
    manual_mother = models.ForeignKey('Mouse', 
        null=True, blank=True, related_name='mmm')

    # This field is almost always set at the time of creation of a new Litter
    litter = models.ForeignKey('Litter', null=True, blank=True)
    
    # track history with simple_history
    history = HistoricalRecords()
    
    # To always sort mice within a cage by name, eg in census view
    class Meta:
        ordering = ['name']
    
    @property
    def new_genotype(self):
        """Return a genotype string by concatenating linked MouseGene objects
        
        If wild_type:
            returns 'WT' (but should probably be a strain)
        If pure_breeder:
            prepends "pure "
        Then it is a list of each linked MouseGene, or "TBD" if there are none.
        """
        if self.wild_type:
            return 'WT'
        
        if self.pure_breeder:
            prefix = 'pure '
        else:
            prefix = ''
        
        qs = self.mousegene_set
        if qs.count() == 0:
            return prefix + '-/-'
        else:
            # Get all the mouse genes that aren't -/-
            res_l = []
            for mg in qs.all():
                if mg.zygosity != MouseGene.zygosity_nn:
                    res_l.append('%s(%s)' % (mg.gene_name, mg.zygosity))
            return prefix + '; '.join(res_l)
    
    def get_cage_history_list(self, only_cage_changes=True):
        """Return list of cage info at every historical timepoint.
        
        The results are sorted from oldest to most recent.
        
        only_cage_changes : if True, then only return history items that
            have a different cage name than the immediately previous item
        
        Returns: list of dicts
            Each dict has keys 'cage__name', 'history_date', 'history_user'
        """
        # List of cages at all historical timepoints
        h_list = self.history.order_by('history_date').all().values(
            'cage__name', 'history_user_id', 'history_date')
        
        # Filter by only those that changed
        if only_cage_changes:
            current_cage = None
            res = []
            for hll in h_list:
                if current_cage is None or hll['cage__name'] != current_cage:
                    res.append(hll)
                    current_cage = hll['cage__name']
            return res
        
        else:
            return h_list
    
    def cage_history_string(self, only_cage_changes=True):
        """Returns a formatted string of the cage history for this mouse"""
        hl = self.get_cage_history_list(only_cage_changes)
        res_l = []
        
        for hll in hl:
            try:
                username = User.objects.get(id=hll['history_user_id']).username
            except User.DoesNotExist:
                username = 'Unknown'
            
            res_l.append('%s Cage: %s  User: %s' % (
                timezone.localtime(hll['history_date']).strftime(
                    '%Y-%m-%d %H:%M:%S'),
                hll['cage__name'],
                username,
            ))
        
        return "<br />\n".join(res_l)
    cage_history_string.allow_tags = True
    cage_history_string.short_description = 'From oldest to newest'

    @property
    def user_or_proprietor(self):
        """Returns the person in charge of this mouse.
        
        This is determined in the following precedence order
            * self.user if it is set
            * self.cage.proprietor if self.cage is set
            * self.litter.breeding_cage.proprietor if self.litter is set
            * Otherwise None

        Probably it would make more sense to use an AutoSlugField here, that
        would update to cage's proprietor after every cage change. Also
        it would be much faster to query the database.
        """
        if self.user:
            return self.user
        
        if self.cage:
            return self.cage.proprietor
        
        if self.litter:
            return self.litter.breeding_cage.proprietor
        
        return None
    
    @property
    def sacked(self):
        return self.sack_date is not None
    
    @property
    def dob(self):
        """Property that returns the DOB of the litter, or manual override.
        
        """
        if self.manual_dob is not None:
            return self.manual_dob
        elif self.litter is not None:
            return self.litter.dob
        else:
            return None
    
    @property
    def mother(self):
        """Property that returns the mother of the litter, or manual override.
        
        """
        if self.manual_mother is not None:
            return self.manual_mother
        elif self.litter is not None:
            return self.litter.mother
        else:
            return None    

    @property
    def father(self):
        """Property that returns the father of the litter, or manual override.
        
        """
        if self.manual_father is not None:
            return self.manual_father
        elif self.litter is not None:
            return self.litter.father
        else:
            return None    
        
    def info(self):
        """Returns a verbose set of information about the mouse.
        
        %NAME% (%SEX% %AGE% %GENOTYPE% %USER%)
        """
        res = "%s (%s " % (self.name, self.get_sex_display())

        # Add age if we know it
        age = self.age()
        if age is not None:
            res += 'P%d ' % age
        
        # Always add genotype
        res += str(self.genotype)
        
        # Add user if we know it
        if self.user:
            res += ' [%s]' % str(self.user)
        
        # Finish
        res += ')'
        return res

    @property
    def progeny(self):
        """Queries database to return all children of this mouse"""
        # Check for mice that have self as a mother or as a father
        # We don't want to want to assume based on self.sex because that
        # may be '?' or set incorrectly
        res1 = Mouse.objects.filter(litter__father=self)
        res2 = Mouse.objects.filter(litter__mother=self)

        if len(res1) > 0 and len(res2) > 0:
            raise ValueError("mouse is both a father and a mother")
        elif len(res1) == 0:
            return res2
        else:
            return res1
    
    def age(self):
        if self.dob is None:
            return None
        today = datetime.date.today()
        return (today - self.dob).days
    
    @property
    def still_in_breeding_cage(self):
        """Returns true if still in the cage it was bred in
        
        This is used to prepend "pup" to the infos.
        """
        if self.litter:
            return self.cage == self.litter.breeding_cage
        else:
            return False
    
    @property 
    def is_breedable_female(self):
        """Returns True if this mouse is female and age is >40 or unknown"""
        my_age = self.age()
        return self.get_sex_display() == 'F' and (my_age is None or my_age > 40)

    @property 
    def is_breedable_male(self):
        """Returns True if this mouse is male and age is >40 or unknown"""
        my_age = self.age()
        return self.get_sex_display() == 'M' and (my_age is None or my_age > 40)

    @property
    def can_be_breeding_mother(self):
        """Returns True if this mouse could be a breeding mother in this cage.
        
        Specifically, returns True if the mouse is_breedable_female and there
        is another mouse in the same cage that is_breedable_male.
        
        This is useful for highlighting mice that are (probably) breeding in
        the CensusView. It eventually could be used to auto-generate the
        "date parents mated" field on litters.
        
        Note that this is distinct from the "breeder" property, which is set
        manually by the user rather than inferred from the "facts on
        the ground".
        """
        if self.is_breedable_female:
            for mouse in self.cage.mouse_set.all():
                if mouse.is_breedable_male:
                    return True
        return False

    @property
    def can_be_breeding_father(self):
        """Returns True if this mouse could be a breeding father in this cage.
        
        See doc for can_be_breeding_mother
        """
        if self.is_breedable_male:
            for mouse in self.cage.mouse_set.all():
                if mouse.is_breedable_female:
                    return True
        return False
    
    def __str__(self):
        return str(self.name)
    
    # This is no longer necessary because the manual_dob field is used
    # to contain this information. In fact we *don't* want to autosave
    # the DOB in this way, because if the litter DOB is changed later, then
    # we want the mouse DOB to automatically update.
    #~ def save(self, *args, **kwargs):
        #~ if self.litter and not self.pk:
            #~ self.manual_dob = self.litter.dob
        #~ return super(Mouse, self).save(*args, **kwargs)

    def save(self, *args, **kwargs):
        # When creating pup in a litter nested inline, automatically place
        # in the breeding cage
        if self.litter and self.litter.breeding_cage and not self.pk:
            self.cage = self.litter.breeding_cage
        return super(Mouse, self).save(*args, **kwargs)

class Gene(models.Model):
    """A particular gene, such as Emx-Cre.
    
    No reference to particular mouse or zygosity here.
    
    The type can be reporter or driver, which mainly just determines
    some things about the way they are sorted.
    """
    name = models.CharField(max_length=50, unique=True)
    
    gene_type_reporter = 'reporter'
    gene_type_driver = 'driver'
    gene_type_choices = (gene_type_reporter, gene_type_driver)
    gene_type_choices_dbl = tuple([(c, c) for c in gene_type_choices])
    gene_type = models.CharField(max_length=20, choices=gene_type_choices_dbl,
        blank=True)
    
    def __str__(self):
        return self.name

class MouseGene(models.Model):
    """Particular gene for a particular mouse
    
    There is a separate instance for every Mouse and every one of the
    genes that it has or may have. So for instance, Mouse M1 can have
    Gene G1 (homo, tested on 10-10) and Gene G2 (het, not tested but
    known). There is just one "Gene" object for each unique Gene (e.g.,
    Emx-Cre).
    
    TODO: Many2Many key from MouseGene to GenotypingSession.
    """
    gene_name = models.ForeignKey(Gene)
    mouse_name = models.ForeignKey(Mouse)
    
    # Zygosity
    zygosity_yy = '+/+'
    zygosity_yn = '+/-'
    zygosity_ym = '+/?'
    zygosity_mn = '?/-'
    zygosity_mm = '?/?'
    zygosity_nn = '-/-' # not sure this one should be allowed
    zygosity_choices = (zygosity_yy, zygosity_yn, zygosity_ym,
        zygosity_mn, zygosity_mm, zygosity_nn)
    zygosity_choices_dbl = tuple([(c, c) for c in zygosity_choices])
    zygosity = models.CharField(max_length=10, choices=zygosity_choices_dbl)
    
    class Meta:
        ordering = ('gene_name__gene_type', 'gene_name__name',)

class Litter(models.Model):
    """Model for Litter.
    
    A Litter is a set of Mice that were born in a Cage. Each Cage should
    only ever have one Litter.
    
    Required fields:
        proprietor (Is this really necessary since we have Cage proprietor?)
        breeding_cage : OneToOne
        father
        mother
    
    Optional fields:
        date_mated
        dob
        date_toeclipped
        date_weaned
        date_checked
        notes
        pcr_info
    """
    # A one-to-one key to Cage, because each Cage can have no more than
    # one litter
    # Not sure whether to set primary_key=True here
    # If we set it true, it implie null=False and unique=True
    # Probably this is good because it will auto-create a Litter for every
    # new Cage, which may save a manual step?
    breeding_cage = models.OneToOneField(Cage,
        on_delete=models.CASCADE,
        primary_key=True)    
    
    # Required field
    proprietor = models.ForeignKey(Person, default=1)

    # ForeignKey to father and mother of Litter
    father = models.ForeignKey('Mouse',
        related_name='bc_father',
        limit_choices_to={'sex': 0})
    mother = models.ForeignKey('Mouse',
        related_name='bc_mother',
        limit_choices_to={'sex': 1})

    # The target genotype is slugged from the genotype of the mother
    # and father
    target_genotype = AutoSlugField(populate_from=slug_target_genotype,
        always_update=True,
        slugify=my_slugify,
    )

    # Optional fields relating to dates
    date_mated = models.DateField('parents mated', null=True, blank=True)
    dob = models.DateField('date of birth', null=True, blank=True)
    date_toeclipped = models.DateField('toe clip', null=True, blank=True)
    date_weaned = models.DateField('weaned', null=True, blank=True)
    date_checked = models.DateField('last checked', null=True, blank=True)
    
    # Other optional fields
    notes = models.CharField(max_length=100, null=True, blank=True)
    pcr_info = models.CharField(max_length=50, null=True, blank=True)

    # track history with simple_history
    history = HistoricalRecords()
    
    def days_since_mating(self):
        if self.date_mated is None:
            return None
        today = datetime.date.today()
        return (today - self.date_mated).days
    
    def age(self):
        if self.dob is None:
            return None
        today = datetime.date.today()
        return (today - self.dob).days

    def __str__(self):
        return self.info
    
    @property
    def info(self):
        """Returns a string like 10@P19"""
        bc_name = self.breeding_cage.name
        try:
            n_pups = len(self.mouse_set.all())
        except AttributeError:
            n_pups = 0
        pup_age = self.age()
        pup_embryonic_age = self.days_since_mating()
        if pup_age is None:
            if pup_embryonic_age is None:
                return '%d pups' % (n_pups)
            else:
                return 'E%s' % (pup_embryonic_age)
        else:
            return '%d@P%s' % (n_pups, pup_age)
    
    def needs_date_mated(self):
        """Returns message if litter has no date_mated.
        
        If the litter does not have a date mated: returns None
        Otherwise: Like all need_* methods, returns dict with 
            trigger, target, and warn dates; as well as a message.
        """
        if self.date_mated or self.dob:
            return None
        
        reference_date = datetime.date.today()

        return {'message': 'specify date mated',
            'trigger': reference_date, 'target': reference_date, 
            'warn': reference_date + datetime.timedelta(days=1)}
    
    def needs_pup_check(self):
        """Returns information about when pup check is needed.
        
        If the litter does not have a date mated: returns None
        Otherwise: Like all need_* methods, returns dict with 
            trigger, target, and warn dates; as well as a message.
        """
        if not self.date_mated or self.dob:
            return None
        
        reference_date = self.date_mated
        trigger = reference_date + datetime.timedelta(days=20)
        target = reference_date + datetime.timedelta(days=25)
        warn = reference_date + datetime.timedelta(days=35)
        
        return {'message': 'pup check',
            'trigger': trigger, 'target': target, 'warn': warn}

    def needs_toe_clip(self):
        """Returns information about when toe clip is needed.
        
        If the litter does not have a date of birth: returns None
        Otherwise: Like all need_* methods, returns dict with 
            trigger, target, and warn dates; as well as a message.
        """        
        if not self.dob or self.date_toeclipped:
            return None
        
        reference_date = self.dob
        trigger = reference_date + datetime.timedelta(days=0)
        target = reference_date + datetime.timedelta(days=7)
        warn = reference_date + datetime.timedelta(days=14)
        
        return {'message': 'toe clip',
            'trigger': trigger, 'target': target, 'warn': warn}

    def needs_genotype(self):
        """Returns information about when genotyping is needed.
        
        If the litter does not have a date of birth: returns None
        Otherwise: Like all need_* methods, returns dict with 
            trigger, target, and warn dates; as well as a message.
        """         
        if not self.dob or self.date_toeclipped:
            return None
        
        reference_date = self.dob
        trigger = reference_date + datetime.timedelta(days=0)
        target = reference_date + datetime.timedelta(days=17)
        warn = reference_date + datetime.timedelta(days=20)
        
        return {'message': 'genotype',
            'trigger': trigger, 'target': target, 'warn': warn}

    def needs_wean(self):
        """Returns information about when weaning is needed.
        
        If the litter does not have a date of birth: returns None
        Otherwise: Like all need_* methods, returns dict with 
            trigger, target, and warn dates; as well as a message.
        """         
        if not self.dob or self.date_weaned:
            return None
        
        reference_date = self.dob
        trigger = reference_date + datetime.timedelta(days=17)
        target = reference_date + datetime.timedelta(days=20)
        warn = reference_date + datetime.timedelta(days=20)
        
        return {'message': 'wean',
            'trigger': trigger, 'target': target, 'warn': warn}

    def auto_needs_message(self):
        """Generates an HTML string with all of the litter auto-needs.
        
        Iterates through all of the needs_* methods and generates
        an HTML string with all of them. Displayed in census view.        
        """
        results_s_l = []
        meth_l = [
            self.needs_date_mated,
            self.needs_pup_check,
            self.needs_toe_clip,
            #~ self.needs_genotype,
            self.needs_wean,
        ]
        today = datetime.date.today()
        
        # Iterate over needs methods
        for meth in meth_l:
            meth_res = meth()
            
            # Continue if no result or not triggered
            if meth_res is None:
                continue
            if meth_res['trigger'] > today:
                continue
            
            # Form the message
            target_date_s = meth_res['target'].strftime('%m/%d')
            full_message_s = '%s on %s' % (meth_res['message'], target_date_s)
            
            # Append with warn tags
            if meth_res['warn'] <= today:
                results_s_l.append('<b>' + full_message_s + '</b>')
            else:
                results_s_l.append(full_message_s)
        
        result_s = '<br />'.join(results_s_l)
        return result_s
    auto_needs_message.allow_tags = True

    def save(self, *args, **kwargs):
        if self.breeding_cage and not self.pk:
            self.proprietor = self.breeding_cage.proprietor
        return super(Litter, self).save(*args, **kwargs)

class SpecialRequest(models.Model):
    cage = models.ForeignKey(Cage)
    message = models.CharField(max_length=150)
    requester = models.ForeignKey(Person, null=True, blank=True,
        related_name='requests_from_me')
    requestee = models.ForeignKey(Person, null=True, blank=True,
        related_name='requests_for_me')
    date_requested = models.DateField('date requested', null=True, blank=True)
    date_completed = models.DateField('date completed', null=True, blank=True)
    
    # track history with simple_history
    history = HistoricalRecords()