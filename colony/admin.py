from django.contrib import admin
from .models import (Mouse, Genotype, Litter, 
    Cage, Person, SpecialRequest, HistoricalMouse, Gene, MouseGene)
# Register your models here.
from django.db.models import Count
import nested_inline.admin
from django.core import urlresolvers
from simple_history.admin import SimpleHistoryAdmin
from django.contrib.admin.views.main import ChangeList
from django import forms

class GeneAdmin(admin.ModelAdmin):
    list_display = ('name', 'gene_type',)

class MouseGeneInline(nested_inline.admin.NestedTabularInline):
    """Nested within Litter, for adding genotyping information"""
    model = MouseGene
    extra = 0

class MouseInline(nested_inline.admin.NestedTabularInline):
    """Inline of pups within litter
    
    This is used for setting the sex, cage, and name of the pups.
    Genotyping and adding pups should be done from litter management.
    """
    model = Mouse
    extra = 0
    
    # Disallow adding mice from the Litter admin
    # This is because we want to add mice using the genotyping form instead
    max_num = 0
    
    # Exclude the stuff that isn't normally specified when adding pups
    exclude = ('manual_dob', 'manual_mother', 'manual_father', 
        'sack_date', 'user', 'breeder', 'genotype', 'pure_breeder', 'wild_type')
    show_change_link = True    

class LitterInline(nested_inline.admin.NestedStackedInline):
    """For adding a Litter to a Cage"""
    model = Litter
    extra = 0
    show_change_link = True
    inlines = [MouseInline]#, MouseGeneInline,]
    readonly_fields = ('link_to_management_page',)

    # We need access to obj.management_link, so have to put it in this
    # function
    def link_to_management_page(self, obj):
        """Generate link to litter management page"""
        link_html_code = u'<a href="%s">%s</a><br />' % (
            obj.management_link, 'Litter management page')
        return link_html_code
    link_to_management_page.allow_tags = True        
    link_to_management_page.short_description = 'Litter management page'

    
    # The purpose of this fieldset is simply to display help text above
    # the Mouse Pup inline, but then we have to explicitly declare all
    # the other fields above it
    fieldsets = (
        (None, {
            'fields': (
                'proprietor', 'father', 'mother', 'date_mated', 'dob',
                'date_toeclipped', 'date_weaned', 'date_checked',
                'date_genotyped',
                'notes', 'pcr_info',
            ),
            #~ 'description': 'Help text goes here',
        }),
        (None, {
            'fields': ('link_to_management_page',),
            'description': (
                '<font size="3">To add pups or provide genotyping ' + 
                'information, go to the litter management page</font>'),
        }),
        (None, {
            'fields': (),
            'description': (
                'Use the lines below to change pup names, sex, or ' + 
                'cage (i.e., weaning). ' +
                'In the future this will all be done on the ' + 
                'litter management page.'
                )
        }),        
    )
    
class SpecialRequestInline(admin.TabularInline):
    model = SpecialRequest
    extra = 1
    show_change_link = True
    inlines = []

class LitterAdminChangeList(ChangeList):
    """Override the Litter changelist to go to Cage instead"""
    def url_for_result(self, result):
        """Clicking the Litter name takes you to the cage page"""
        pk = result.breeding_cage.pk
        return '/admin/colony/cage/%d' % pk

class LitterAdmin(admin.ModelAdmin):
    list_display = ('name', 'dob', 'date_toeclipped', 'cross', 'info',
        'get_special_request_message', 'cage_notes', 'notes', 'date_genotyped',)
    inlines = [MouseInline] 
    list_editable = ('notes', 'date_genotyped')
    list_filter = ('breeding_cage__proprietor',)
    readonly_fields = ('target_genotype', 'info', 'cross', 'age', 
        'get_special_request_message', 'name',)
    ordering = ('dob', 'date_toeclipped', 'breeding_cage__name',)

    def get_changelist(self, request, **kwargs):
        """Overrule changelist so that clicking litter name goes to page"""
        return LitterAdminChangeList

    def get_queryset(self, request):
        """Only return litters that are born but haven't been genotyped."""
        qs = super(LitterAdmin, self).get_queryset(request)
        return qs.filter(date_genotyped=None, dob__isnull=False)

    def name(self, obj):
        return str(obj)

    def get_special_request_message(self, obj):
        return obj.breeding_cage.get_special_request_message()
    get_special_request_message.allow_tags = True
    get_special_request_message.short_description = 'Requests'

    def cage_notes(self, obj):
        return obj.breeding_cage.notes

    def cross(self, obj):
        return obj.breeding_cage.printable_relevant_genesets
    cross.short_description = 'Cross'
    
    def n_pups(self, obj):
        return obj.mouse_set.count()
    n_pups.short_description = 'Size'

class DefunctFilter(admin.SimpleListFilter):
    """By default, filter by defunct=False
    
    https://www.elements.nl/2015/03/16/getting-the-most-out-of-django-admin-filters/
    """
    title = 'whether the cage is defunct'
    parameter_name = 'defunct'
    
    def lookups(self, request, model_admin):
        """Map the choice strings in the URL to human-readable text
        
        Note that an "All" choice is always presented, but we're breaking
        it, so we need no provide an "Actually All".
        """
        return (
            ('no', 'Active'),
            ('yes', 'Defunct'),
            ('all', 'Actually All'),
        )
    
    def queryset(self, request, queryset):
        """Filter by the selected self.value()"""
        filter_value = self.value()
        if filter_value == 'no':
            return queryset.filter(defunct=False)
        elif filter_value == 'yes':
            return queryset.filter(defunct=True)
        elif filter_value == 'all':
            return queryset
        else:
            raise ValueError("unexpected value %s" % filter_value)
    
    def value(self):
        """Override value() to be 'no' by default
        
        Bug here because selecting the hardwired "All" option will still
        choose 'no'.
        """
        value = super(DefunctFilter, self).value()
        if value is None:
            value = 'no'
        return value

class AddMiceToCageForm(forms.ModelForm):
    """Special form to allow adding mice from the cage admin page.
    
    Basically we just add a ModelMultipleChoiceField, populated with
    the current mouse set. Upon saving, we update the cage field on
    each mouse.
    
    References:
    Adapted from here: http://stackoverflow.com/questions/6034047/one-to-many-inline-select-with-django-admin
    See also: http://stackoverflow.com/questions/17948018/django-admin-add-custom-form-fields-that-are-not-part-of-the-model
    The trick of adding fields = '__all__' comes from the second link
    """
    # http://stackoverflow.com/questions/6034047/one-to-many-inline-select-with-django-admin
    class Meta:
        model = Cage
        
        # Without this, complains that fields or exclude needs to be set
        fields = '__all__'
    
    # Custom form field for selecting multiple mice
    add_mouse_to_cage = forms.ModelChoiceField(required=False,
        queryset=Mouse.objects.filter(sack_date__isnull=True).all())
    
    # Override __init__ if you want to specify initial
    
    def save(self, commit=True, *args, **kwargs):
        """Add the selected mouse to this cage.
        
        Sets the selected mouse's cage attribute to this cage.
        commit argument is not handled
        
        This seems to correctly save the "add_mouse_to_cage" form
        field only if a mouse was actually selected.
        """
        # Call the superclass save function but don't commit
        # Not even sure what this does other than set up `instance`
        instance = super(AddMiceToCageForm, self).save(commit=False)

        # Get the selected mouse, if any
        selected_mouse = self.cleaned_data['add_mouse_to_cage']
        
        if selected_mouse:        
            # Set the selected mouse's cage attribute to this cage
            selected_mouse.cage = instance
            
            # Save it, in order to trigger any custom save stuff
            # (important for historical mouse records)
            selected_mouse.save()
        
        return instance        

class CageAdmin(nested_inline.admin.NestedModelAdmin):
    """Admin page for the Cage object.

    A custom form is used to allow adding mice using multiple
    selection, as opposed to individually going to each mouse page.
    """
    # Columns in the list page
    list_display = ('name', 'proprietor', 'litter', 
        'target_genotype', 'link_to_mice', 
        'auto_needs_message', 'notes',)
    
    # The ones that are editable
    list_editable = ('notes', )
    
    # This allows filtering by proprietor name and defunctness
    # Also filter by genotype of contained mice
    list_filter = ('proprietor__name', DefunctFilter, 
        'mouse__mousegene__gene_name', 'location',)
    
    # Allow searching cages by mouse info
    # Searching by litter__target_genotype allows us to include relevant
    # breeding cages even if the father is out of the picture.
    search_fields = ('name', 
        'mouse__name', 'litter__target_genotype', 
        'mouse__mousegene__gene_name__name')
    
    # Sorting in the list page
    ordering = ('defunct', 'name',)
    
    # The readonly fields
    readonly_fields = ('infos', 'target_genotype', 
        'link_to_mice', 'auto_needs_message', 'litter__target_genotype',
        'target_genotype')
    
    # Litter is an inline
    inlines = [LitterInline, SpecialRequestInline]

    # A special form for adding mice
    form = AddMiceToCageForm

    # Pagination to save time
    list_per_page = 20

    ## Define what shows up on the individual cage admin page
    # Clickable links to every mouse in the cage
    def link_to_mice(self, obj):
        """Generate HTML links for every mouse in the cage"""
        link_html_code = ''
        for child in obj.mouse_set.order_by('name').all():
            child_link = urlresolvers.reverse("admin:colony_mouse_change", 
                args=[child.id])
            child_info = child.info()
            if child_info is None or child_info == '':
                child_info = 'mouse'
            link_html_code += u'<a href="%s">%s</a><br />' % (
                child_link, child_info)
        return link_html_code
    link_to_mice.allow_tags = True        
    link_to_mice.short_description = 'Mice in this cage'
    
    # Arrangement of fields on individual cage admin page
    fieldsets = (
        (None, {
            'fields': ('name', 'location', 'proprietor',),
            'description': 'Required properties',
        }),
        (None, {
            'fields': ('notes', 'defunct',),
            'description': 'Optional properties',
        }),        
        (None, {
            'fields': ('link_to_mice', 'add_mouse_to_cage',),
            'description': 'Mice currently in this cage, and option to add more',
        }),                     
        (None, {
            'fields': ('target_genotype', 'auto_needs_message',),
            'description': 'Litter husbandry information',
        }),
    )

class SackFilter(admin.SimpleListFilter):
    title = 'Sacked'
    parameter_name = 'sac date'
    
    def lookups(self, request, model_admin):
            return(
                ('yes', 'yes'),
                ('no', 'no'),
            )
        
    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.filter(sack_date__isnull=False)
        
        if self.value() == 'no':
            return queryset.filter(sack_date__isnull=True)

class MouseAdmin(admin.ModelAdmin):
    """Mouse administration: list view and individual admin page"""
    ## List view for mice
    # The columns that show up
    list_display = ('name', 'user', 'dob', 'age', 'sacked', 'sex', 'cage', 
        'new_genotype', 'notes',)
    list_editable = ('notes',)
    readonly_fields = ('info', 'age', 'dob', 'mother', 'father', 'sacked', 
        'link_to_mother', 'link_to_father', 'link_to_progeny',
        'link_to_cage', 'cage_history_string', 'litter_management',
        'old_genotype', 'new_genotype',)

    # How to filter and search
    list_filter = ['cage__proprietor', 'user', 'breeder', SackFilter, 
        'mousegene__gene_name',
    ]
    search_fields = ('name', 'mousegene__gene_name__name')
    
    # How it is sorted by default
    ordering = ('name',)
    
    # Pagination to save time
    list_per_page = 20

    ## Ordering for choosing cage for mouse
    # http://stackoverflow.com/questions/8992865/django-admin-sort-foreign-key-field-list
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Would like to exclude defunct cages here but I think people are
        # moving mice to defunct cages
        if db_field.name == "cage":
            kwargs["queryset"] = Cage.objects.order_by('name')
        return super(MouseAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

    ## Create fields that are HTML links to other mice
    # http://stackoverflow.com/questions/28832897/link-in-django-admin-to-foreign-key-object
    def link_to_mother(self, obj):
        link = urlresolvers.reverse("admin:colony_mouse_change", 
            args=[obj.mother.id])
        return u'<a href="%s">%s</a>' % (link, obj.mother.name)
    link_to_mother.allow_tags=True    
    
    def link_to_father(self, obj):
        link = urlresolvers.reverse("admin:colony_mouse_change", 
            args=[obj.father.id])
        return u'<a href="%s">%s</a>' % (link, obj.father.name)
    link_to_father.allow_tags=True    

    def link_to_cage(self, obj):
        link = urlresolvers.reverse("admin:colony_cage_change", 
            args=[obj.cage.id])
        return u'<a href="%s">%s</a>' % (link, obj.cage.name)
    link_to_cage.allow_tags=True    

    def link_to_progeny(self, obj):
        """Generate HTML links for every child"""
        link_html_code = ''
        for child in obj.progeny:
            child_link = urlresolvers.reverse("admin:colony_mouse_change", 
                args=[child.id])
            child_info = child.info()
            if child_info is None or child_info == '':
                child_info = 'pup'
            link_html_code += u'<a href="%s">%s</a><br />' % (
                child_link, child_info)
        return link_html_code
    link_to_progeny.allow_tags=True    

    def litter_management(self, obj):
        """Generate link to litter management page"""
        link_html_code = u'<a href="%s">%s</a><br />' % (
            obj.litter.management_link, 'Litter management page')
        return link_html_code
    litter_management.allow_tags = True        

    # Shortcuts to display read-only genotype
    def old_genotype(self, obj):
        return obj.genotype
    old_genotype.short_description = 'Old genotype (historical mice only)'
    
    def new_genotype(self, obj):
        return obj.new_genotype
    new_genotype.short_description = 'Genotype'

    ## Individual Mouse admin page
    fieldsets = (
        (None, {
            'fields': ('name', 'sex',),
            'description': 'Required properties',
        }),
        (None, {
            'fields': ('cage', 'link_to_cage', 'sack_date', 
                'user', 'notes',),
            'description': 'Optional properties',
        }),        
        (None, {
            'fields': ('new_genotype', 'pure_breeder', 'wild_type', 
                'litter_management', 'old_genotype',),
            'description': 'Genotyping',
        }),             
        (None, {
            'fields': ('link_to_mother', 'link_to_father', 'link_to_progeny',),
            'description': 'Genealogy',
        }),     
        (None, {
            'fields': ('cage_history_string', ),
            'description': 'Historical cage records',
        }),                
        (None, {
            'fields': ('age', 'manual_father', 'manual_mother', 'manual_dob',),
            'description': (
                'These properties are normally derived from the litter. '
                'Override mother, father, and DOB here if necessary.'),
        }),        
            (None, {
            'fields': (),
            'description': (
                'Add a gene for a newly acquired pure breeder here. ' +
                'For progeny mice, genotyping info should instead be added ' + 
                'using the "litter management page" linked above.')
        }),    
    )
    
    # Inlines for adding mouse genes
    inlines = [MouseGeneInline,]
    
class MouseGeneAdmin(admin.ModelAdmin):
    list_display = ('mouse_name', 'gene_name', 'zygosity',)

class GenotypeAdmin(admin.ModelAdmin):
    ordering = ('name',)

    ## Define what shows up on the individual mouse admin page
    fieldsets = (
        (None, {
            'fields': ('name',),
            'description': 'ANY CHANGE YOU MAKE HERE WILL AFFECT EVERY '
                'MOUSE WITH THIS GENOTYPE! This is almost never what you '
                'want to do. If you just want to change one mouse\'s '
                'genotype, then close this window, and choose a different '
                'genotype from the dropdown list, or click the plus button '
                'to create a new one.',
        }),
    )

class PersonAdmin(admin.ModelAdmin):
    ordering = ('name',)

class SpecialRequestAdmin(admin.ModelAdmin):
    list_display = ('cage', 'requester', 'requestee', 'date_requested', 
        'date_completed', 'message',)

class HistoricalMouseAdmin(admin.ModelAdmin):
    list_filter = ('cage__name', 'name',)
    search_fields = ('name', 'cage__name')
    list_display = ('history_date', 'history_user', 'name', 'cage', 'notes',
        'genotype',)
    change_list_template = 'admin/colony/historicalmouse/change_list.html'


admin.site.register(HistoricalMouse, HistoricalMouseAdmin)
admin.site.register(Mouse, MouseAdmin)
admin.site.register(Gene, GeneAdmin)
admin.site.register(MouseGene, MouseGeneAdmin)
admin.site.register(Genotype, GenotypeAdmin)
admin.site.register(Litter, LitterAdmin)
admin.site.register(Cage, CageAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.register(SpecialRequest, SpecialRequestAdmin)