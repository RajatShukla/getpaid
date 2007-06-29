"""

cart-review checkout

$Id$
"""

"""
random notes

get order

 - create order [ entry points ]
 - dispatch on workflow state
 
Order Workflow

  - created
     - system invariant - make sure we don't create multiple orders from the same cart, need to create cart_id, retrieve order by user_id, cart_id
     - automatic ready
     
  - ready
     - user submit
     
  - pending
     - automatic declined     
     - automatic accepted
     
  - declined
     - user submit pending

  - accepted
     - admin submit processed
     
  - processed

  - re
  
  - status
  
allow linear progression

carry hidden to force transition to required, allow linear links to be used though

"""

import random, sys
from cPickle import loads, dumps

from zope.formlib import form
from zope.schema import getFieldsInOrder
from zope import component

from getpaid.core import interfaces
from getpaid.core.order import Order

from ore.member.browser import MemberContextEdit

from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from base import BaseFormView, BaseView



class PropertyBag(object):

    schema = interfaces.IUserPaymentInformation
    title = "Payment Details"
    description = ""
    
    def initclass( cls ):
        for field_name, field in getFieldsInOrder( interfaces.IUserPaymentInformation ):
            setattr( cls, field_name, field.default )
    
    initclass = classmethod( initclass )

PropertyBag.initclass()

class ImmutableBag( object ):

    def initfrom( self, other, iface ):
        for field_name, field in getFieldsInOrder( iface ):
            setattr( self, field_name, field.get( other ) )
        return self

class CheckoutConfirmed( BrowserView, BaseView ):
    pass
    
class CheckoutPayment( MemberContextEdit ):
    """
    browser view for collecting credit card information and submitting it to
    a processor.
    """
    form_fields = None
    template = ZopeTwoPageTemplateFile("templates/checkout-billing-info.pt")

    _next_url = None

    def render( self ):
        if self._next_url:
            self.request.RESPONSE.redirect( self._next_url )
            return ""
        return super( CheckoutPayment, self).render()
    
    @form.action("Make Payment")
    def makePayment( self, action, data ):
        """ create an order, and submit to the processor
        """
        import pdb; pdb.set_trace()
        manage_options = IGetPaidManagementOptions( self.context )
        processor_name = manage_options.payment_processor
        
        if not processor_name:
            raise RuntimeError( "No Payment Processor Specified" )

        processor = component.getAdapter( self.context,
                                          interfaces.IPaymentProcessor,
                                          processor_name )
        order = self.createOrder()
        
        processor.authorize( order, self.adapters[ interfaces.IUserPaymentInformation ]  )
        self._next_url = self.getNextURL( order )

    def createOrder( self ):
        order_manager = component.getUtility( interfaces.IOrderManager )
        order = Order()

        shopping_cart = component.getUtility( interfaces.IShoppingCartUtility ).get( self.context )
        # shopping cart is attached to the session, but we want to switch the storage to the persistent
        # zodb, we pickle to get a clean copy to store.
        order.shopping_cart = loads( dumps( shopping_cart ) )
        order.shipping_address = ImmutableBag().initfrom( self.adapters[ interfaces.IShippingAddress ],
                                                          interfaces.IShippingAddress ) 
        order.billing_address = ImmutableBag().initfrom( self.adapters[ interfaces.IBillingAddress ],
                                                         interfaces.IBillingAddress )
        while 1:
            order_id =  str( random.randint( 0, sys.maxint ) )
            if order_manager.get( order_id ) is None:
                break
        order.order_id = order_id
        order.finance_workflow.fireTransition( "create" )
        order_manager.store( order )
        return order

    def getNextURL( self, order ):
        state = order.finance_state
        f_states = interfaces.finance_states
        base_url = self.context.absolute_url()
        
        if state in ( f_states.CANCELLED,
                      f_states.CANCELLED_BY_PROCESSOR,
                      f_states.PAYMENT_DECLINED ):
            return base_url + '@@checkout-error'

        elif state in ( f_states.CHARGEABLE,
                        f_states.CHARGED ):
            return base_url + '@@checkout-confirmed'
            

    def getFormFields( self, user ):
        form_fields = super( CheckoutPayment, self).getFormFields(user)
        self.adapters[ interfaces.IUserPaymentInformation ] = self.billing_info
        return form_fields + form.Fields( interfaces.IUserPaymentInformation )

    def __call__( self ):
        self.billing_info = PropertyBag()
        try:
            return super( CheckoutPayment, self).__call__()
        except:
            import sys,pdb,traceback
            traceback.print_exc()
            pdb.post_mortem( sys.exc_info()[-1] )
            raise

    def setUpWidgets( self, ignore_request=False ):
        self.adapters = self.adapters is not None and self.adapters or {}
        self.widgets = form.setUpEditWidgets(
            self.form_fields, self.prefix, self.context, self.request,
            adapters=self.adapters, ignore_request=ignore_request
            )
    


    
