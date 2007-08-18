"""
$Id$
"""

from zope.interface import Interface, Attribute, classImplements
from zope import schema
from zope.app.event.interfaces import IObjectEvent
from zope.app.container.interfaces import IContainer
from zope.schema.interfaces import ITextLine
from fields import PhoneNumber, CreditCardNumber
from zope.i18nmessageid import MessageFactory
_ = MessageFactory('getpaid')


#################################
# Where to Buy Stuff

class IStore( Interface ):
    """ represents a getpaid installation, should be a local site w/ getpaid local components installed
    """

#################################
# Stuff To Buy

class IPayable( Interface ):
    """
    An object which can be paid for. Payables are typically gotten via adapation between
    a context and the request, to allow for pricing / display customization on a user
    basis.
    """
    
    made_payable_by = schema.TextLine(
        title = _(u"Made Payable By"),
        readonly = True,
        required = False
        )
    
    product_code = schema.TextLine( title = _(u"Product Code"),
                        description=_(u"An organization's unique product identifier (not required since shopping cart uses content UID internally)"),
                        required=False
                        )
    price = schema.Float( title = _(u"Price"), required=True)

class IDonationContent( IPayable ):
    """ Donation
    """
    donation_text = schema.TextLine( title = _(u"Donation Description"),
                        description=_(u"Very brief 50 character text (that shows up in portlet)"),
                        required=True,
                        max_length=50)

class ISubscription( IPayable ):
    """ Subscription
    """

class IBuyableContent( IPayable ):
    """ Purchasable Content Delivered Virtually
    """
    
class IPremiumContent( Interface ):
    """ Premium Content for Subscriptions
    """

class IPhysicalPayable( IPayable ):
    """
    """

class IShippableContent( IPayable ):
    """ Shippable Content
    """
    dimensions = schema.TextLine( title = _(u"Dimensions"))
    sku = schema.TextLine( title = _(u"Product SKU"))
    
    def getShipWeight( self ):
        """ Shipping Weight
        """

#################################
# Events

class IPayableCreationEvent( IObjectEvent ):
    """ sent out when a payable is created
    """

    payable = Attribute("object implementing payable interface")
    
    payable_interface = Attribute("payable interface the object implements")


class IPayableAuditLog( Interface ):
    """ ordered container of changes, most recent first, hook on events.
    """


#################################
# Stuff to Process Payments

class IPaymentProcessor( Interface ):
    """ A Payment Processor

    a processor can keep processor specific information on an orders
    annotations. 
    """ 

    def authorize( order, payment_information ):
        """
        authorize an order, using payment information.

        (XXX - processors should decorate orders with processor name )
        """

    def capture( order, amount ):
        """
        capture amount from order.
        """

    def refund( order, amount ):
        """
        reset
        """
    
class IRecurringPaymentProcessor( IPaymentProcessor ):
    """ a payment processor that can handle recurring line items
    """
    
class IPaymentProcessorOptions( Interface ):
    """ Options for a Processor

    """
    
#################################
# Info needed for payment processing

    
class ILineItem( Interface ):
    """
    An Item in a Cart
    """
    item_id = schema.TextLine( title = _(u"Unique Item Id"))
    name = schema.TextLine(title = _(u"Name"))
    description = schema.TextLine( title = _(u"Description"))
    cost = schema.Float( title = _(u"Cost"))
    quantity = schema.Int( title = _(u"Quantity"))


class ILineItemFactory( Interface ):
    """ encapsulation of creating and adding a line item to a line item container
    from a payable.
    """
    
    def create( payable ):
        """
        create a payable from a line item
        """

class ILineItemContainer( IContainer ):
    """ A container for line items
    """
    
class IPayableLineItem( ILineItem ):
    """
    A line item linked to a payable
    """

    def resolve( ):
        """ return the payable object, or None if can't be found.
        """

class IRecurringLineItem( IPayableLineItem ):

    period = schema.Int( title = _(u"Period as a timedelta"))
    

class IGiftCertificate( ILineItem ):
    """ A Gift Certificate
    """

#################################
# Shopping Cart Stuff

class IShoppingCartUtility( Interface ):

    def get( create=False ):
        """
        return the user's shopping cart or none if not found.
        if create is passed then create a new one if one isn't found
        """

    def destroy( ):
        """
        remove the current's users cart from the session if it exists
        """
        
class IShoppingCart( ILineItemContainer ):
    """ A Shopping Cart 
    """


#################################
# Shipping

class IShipmentContainer(  IContainer ):
    """ a container for shipments
    """

class IShipment( ILineItemContainer ):
    """ a (partial|complete) shipment of ishippable line items of an order
    """

class IShippingMethod( Interface ):

    def getCost( order ):
        """ get the shipping cost for an order
        """

#################################
# Tax Utility

class ITaxUtility( Interface ):

    def getCost( order ):
        """ return the tax amount for an order
        """
        

#################################
# Payment Information Details

class IAddress( Interface ):
    """ a physical address
    """
    first_line = schema.TextLine( title = _(u"First Line"), description=_(u"Please Enter Your Address"))
    second_line = schema.TextLine( title = _(u"Second Line"), required=False )
    city = schema.TextLine( title = _(u"City") )
    state = schema.Choice( title = _(u"State"),
                             vocabulary="getpaid.states")
    country = schema.Choice( title = _(u"Country"),
                               vocabulary = "getpaid.countries")
    postal_code = schema.TextLine( title = _(u"Zip Code"))

class IShippingAddress( Interface ):
    """ where to send goods
    """
    ship_first_line = schema.TextLine( title = _(u"First Line"))
    ship_second_line = schema.TextLine( title = _(u"Second Line"), required=False )
    ship_city = schema.TextLine( title = _(u"City") )
    ship_state = schema.Choice( title = _(u"State"),
                                  vocabulary="getpaid.states" )
    ship_country = schema.Choice( title = _(u"Country"),
                                    vocabulary = "getpaid.countries")
    ship_postal_code = schema.TextLine( title = _(u"Zip Code"))

class IBillingAddress( Interface ):
    """ where to bill 
    """
    bill_first_line = schema.TextLine( title = _(u"First Line"))
    bill_second_line = schema.TextLine( title = _(u"Second Line"), required=False )
    bill_city = schema.TextLine( title = _(u"City") )
    bill_state = schema.Choice( title = _(u"State"),
                                  vocabulary="getpaid.states" )
    bill_country = schema.Choice( title = _(u"Country"),
                                    vocabulary = "getpaid.countries")
    bill_postal_code = schema.TextLine( title = _(u"Zip Code"))

class IUserPaymentInformation( Interface ):
    """ A User's payment information to be optionally collected by the
    payment processor view.
    """

    name_on_card = schema.TextLine( title = _(u"Card Holder Name"))
    phone_number = PhoneNumber( title = _(u"Phone Number"),
                                description = _(u"Only digits allowed"))
    # DONT STORED PERSISTENTLY
    credit_card_type = schema.Choice( title = _(u"Credit Card Type"),
                                      values = ( u"Visa",
                                                 u"MasterCard",
                                                 u"Discover",
                                                 u"American Express" ) )

    credit_card = CreditCardNumber( title = _(u"Credit Card Number"),
                                    description = _(u"Only digits allowed"))
    cc_expiration = schema.TextLine( title = _(u"Credit Card Expiration Date"))
    cc_cvc = schema.TextLine(title = _(u"Credit Card Verfication Number"))


    
class IPaymentTransaction( ILineItemContainer ):
    """  A Payment that's been applied
    """

    status = schema.Choice( title = _(u"Payment Status"),
                            values = ( _(u"Accepted"),
                                       _(u"Declined"),
                                       _(u"Refunded") ) )
    
class IPersistentOptions( Interface ):
    """ interface
    """

#################################
# Orders

class IOrderManager( Interface ):
    """ persistent utility for storage and query of orders
    """

    def query( **kw ):
        """ query the orders, XXX extract order query interface
        """

    def get( order_id ):
        """ retrieve an order
        """

    def store( order ):
        """ save an order
        """

class IOrder( Interface ):
    """ captures information, and is a container to multiple workflows
    """
    user_id = schema.ASCIILine( title = _(u"Customer Id"), readonly=True )
    shipping_address = schema.Object( IShippingAddress, required=False)
    billing_address  = schema.Object( IBillingAddress )
    shopping_cart = schema.Object( IShoppingCart )
    finance_state = schema.TextLine( title = _(u"Finance State"), readonly=True)
    fufillment_state = schema.TextLine( title = _(u"Fufillment State"), readonly=True)
    processor_order_id = schema.ASCIILine( title = _(u"Processor Order Id") )
    processor_id = schema.ASCIILine( readonly=True )


# Various Order Classification Markers..
# a shippable order for exmaple contains something an ishippable,
# virtual order contains only ttw deliverables
# donation orders contain donations
# recurrence for not yet implement contains recurring line items
# the only mutual exclusive we have at the moment we these is shippable/virtual


class IShippableOrder( Interface ):
    """ marker interface for orders which need shipping """

class IRecurringOrder( Interface ):
    """ marker interface for orders containing recurring line items """

class IVirtualOrder( Interface ):
    """ marker inteface for orders which are delivered virtually """

class IDonationOrder( Interface ):
    """ marker interface for orders which contain donations"""


    
class IOrderWorkflowLog( Interface ):
    """ an event log based history of an order's workflow
    """
    def __iter__( ):
        """ iterate through records of the order's history, latest to oldest.
        """

    def last( ):
        """ get the last change to the order
        """

class IOrderWorkflowEntry( Interface ):
    """ a record describing a change in an order's workflow history
    """
    changed_by = schema.ASCIILine( title = _(u"Changed By"), readonly = True )
    change_date = schema.ASCIILine( title = _(u"Change Date"), readonly = True)
    comment = schema.ASCIILine( title = _(u"Comment"), readonly = True, required=False )
    new_state = schema.ASCIILine( title = _(u"New State"), readonly = True)
    previous_state = schema.ASCIILine( title = _(u"Previous State"), readonly = True )
    transition = schema.ASCIILine( title = u"", readonly = True)
    # change type?? (workflow, user


class IPhoneNumber(ITextLine):
    """A Text line field that handles phone number input."""
classImplements(PhoneNumber,IPhoneNumber)


class ICreditCardNumber(ITextLine):
    """A Text line field that handles credit card input."""
classImplements(CreditCardNumber,ICreditCardNumber)


class keys:
    """ public annotation keys and static variables
    """

    # how much of the order have we charged
    capture_amount= 'getpaid.capture_amount'
    
    # processor specific txn id for an order
    processor_txn_id = 'getpaid.processor.uid'
    
    # name of processor adapter
    processor_name = 'getpaid.processor.name'

    # sucessful call to a processor
    results_success = 1
    results_async = 2
    
class workflow_states:

    class order:
        # order workflows are executed in parallel

        class finance:
            # name of parallel workflow            
            name = "order.finance"

            REVIEWING = 'REVIEWING'
            CHARGEABLE = 'CHARGEABLE'
            CHARGING = 'CHARGING'
            CHARGED = 'CHARGED'
            REFUNDED = 'REFUNDED'
            PAYMENT_DECLINED = 'PAYMENT_DECLINED'
            CANCELLED = 'CANCELLED'
            CANCELLED_BY_PROCESSOR = 'CANCELLED_BY_PROCESSOR'
            
        class fulfillment:
            # name of parallel workflow
            name = "order.fulfillment"            

            NEW = 'NEW'
            PROCESSING = 'PROCESSING'
            DELIVERED = 'DELIVERED'
            WILL_NOT_DELIVER = 'WILL_NOT_DELIVER'
            
    class item:
        NEW = 'NEW'
        PROCESSING = 'PROCESSING'
        DELIVER_VIRTUAL = 'DELIVERVIRTUAL'
        CANCELLED = 'CANCELLED'
        SHIPPED = 'SHIPPED'
        #RETURNING = 'RETURNING'
        #RETURNED = 'RETURNED'
        REFUNDING = 'REFUNDING'
        REFUNDED = 'REFUNDED'

    class shipment:
        NEW = 'NEW'
        CHARGING = 'CHARGING'
        DECLINED = 'DECLINED'
        DELIVERED = 'DELIVERED'
        SHIPPED = 'SHIPPED'
        SHIPPABLE = 'SHIPPABLE'
        CHARGED = 'CHARGED'
            
