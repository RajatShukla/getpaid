"""
$Id$
"""

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from Products.Five.browser import BrowserView
from Products.Five.formlib import formbase
from Products.PloneGetPaid import interfaces

from zope import component
from zope.formlib import form
from zope.app.form.browser import MultiSelectWidget

import getpaid.core.interfaces as igetpaid

from ore.member.browser import SchemaSelectWidget as SelectWidgetFactory

from base import BaseView

class Overview( BrowserView ):
    """ overview of entire system
    """

class BaseSettingsForm( formbase.EditForm, BaseView ):

    options = None
    
    def __init__( self, context, request ):
        self.context = context
        self.request = request
        self.setupLocale( request )
        self.setupEnvironment( request )    

    def update( self ):
        try:
            interface = iter( self.form_fields ).next().field.interface
        except StopIteration:
            interface = None
        if interface is not None:
            self.adapters = { interface : interfaces.IGetPaidManagementOptions( self.context ) } 
        super( BaseSettingsForm, self).update()
        
# Profile
class Identification( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-identification.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementIdentificationOptions)
    

#Configure
class ContentTypes( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-content-types.pt")
    form_fields = form.Fields( interfaces.IGetPaidManagementContentTypes )

    form_fields['buyable_types'].custom_widget = SelectWidgetFactory
    form_fields['premium_types'].custom_widget = SelectWidgetFactory
    form_fields['donate_types'].custom_widget = SelectWidgetFactory
    form_fields['shippable_types'].custom_widget = SelectWidgetFactory


class ShippingOptions( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-shipping-options.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementShippingOptions)

class PaymentOptions( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-payment-options.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementPaymentOptions)
    form_fields['accepted_credit_cards'].custom_widget = SelectWidgetFactory

class PaymentProcessor( BaseSettingsForm ):
    """
    get paid management interface, slightly different because our form fields
    are dynamically set based on the store's setting for a payment processor.
    """
    
    template = ZopeTwoPageTemplateFile("templates/admin-payment-processor.pt")
    form_fields = form.Fields()

    def __call__( self ):
        self.setupProcessorOptions()
        return super( PaymentProcessor, self).__call__()
        
    def setupProcessorOptions( self ):
        manage_options = interfaces.IGetPaidManagementOptions( self.context )
        
        processor_name = manage_options.payment_processor
        if not processor_name:
            self.status = "Please Select Payment Processor in Payment Options Settings"
            return

        processor = component.getAdapter( self.context,
                                          igetpaid.IPaymentProcessor,
                                          processor_name )
        
        self.form_fields = form.Fields( processor.options_interface )
        
# Order Management
class CustomerInformation( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-customer-information.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementCustomerInformation)

class PaymentProcessing( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-payment-processing.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementPaymentProcessing)
        
class WeightUnits( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-weight-units.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementWeightUnits)
        
class SessionTimeout( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-session-timeout.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementSessionTimeout)

class SalesTax( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-sales-tax.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementSalesTaxOptions)
                
#Currency        
class Currency( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-currency.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementCurrencyOptions)

#Emails
class Email( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-email.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementEmailOptions)

class MerchantNotification( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-merchant-notification.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementMerchantNotificationOptions)

class CustomerNotification( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-customer-notification.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementCustomerNotificationOptions)

#Customize Header/Footer        
class LegalDisclaimers( BaseSettingsForm ):
    """
    get paid management interface
    """
    template = ZopeTwoPageTemplateFile("templates/admin-legal-disclaimers.pt")
    form_fields = form.Fields(interfaces.IGetPaidManagementLegalDisclaimerOptions)
        
        
       

