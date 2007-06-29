"""
$Id$
"""

from zope.interface import Interface
from zope import schema
from zope.app.container.interfaces import IContainer
from ore.member.interfaces import IMemberSchema

#################################
# Stuff To Buy

class IPayable( Interface ):
    """
    An object which can be paid for. Payables are typically gotten via adapation between
    a context and the request, to allow for pricing / display customization on a user
    basis.
    """
    madePayableBy = schema.TextLine( title=u"Made Payable By",
                        description=u"(eventually will be id of logged-in user)",
                        required=False
                        )
    productCode = schema.TextLine( title=u"Product Code",
                        description=u"An organization's unique product identifier (not required since shopping cart uses content UID internally)",
                        required=False
                        )
    price = schema.Float( title=u"Price", required=True)

class IDonationContent( IPayable ):
    """ Donation
    """
    donationText = schema.TextLine( title=u"Donation Description",
                        description=u"Very brief 50 character text (that shows up in portlet)",
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
    dimensions = schema.TextLine( title=u"Dimensions")
    sku = schema.TextLine( title=u"Product SKU")
    
    def getShipWeight( self ):
        """ Shipping Weight
        """

class IPayableAuditLog( Interface ):
    """ ordered container of changes, most recent first, hook on events.
    """
    #modification_date = 
    #changed_by =


#################################
# Stuff to Process Payments
class IPaymentProcessor( Interface ):
    """ A Payment Processor
    """ 

class IPaymentProcessorOptions( Interface ):
    """ Options for a Processor

    """
    
#################################
# Info needed for payment processing


    
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

class ILineItem( Interface ):
    """
    An Item in a Cart
    """
    item_id = schema.TextLine( title= u"Unique Item Id")
    name = schema.TextLine(title = u"Name")
    description = schema.TextLine( title = u"Description")
    cost = schema.Float( title=u"Cost")
    quantity = schema.Int( title = u"Quantity")
    
class IPayableLineItem( ILineItem ):
    """
    A line item linked to a payable
    """

    def resolve( context ):
        """ return the payable object
        """

class IGiftCertificate( ILineItem ):
    """ A Gift Certificate
    """

class ILineItemContainer( IContainer ):
    """ A container for line items
    """

class IShoppingCart( ILineItemContainer ):
    """ A Shopping Cart 
    """


#################################
# Shipping Method Utility

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
    first_line = schema.TextLine( title = u"First Line")
    second_line = schema.TextLine( title = u"Second Line" )
    state = schema.TextLine( title = u"State ")
    city = schema.TextLine( title = u"City" )
    country = schema.TextLine( title = u"Country")
    postal_code = schema.TextLine( title = u"Zip Code")

class IShippingAddress( IMemberSchema ):
    """ where to send goods
    """
    ship_first_line = schema.TextLine( title = u"First Line")
    ship_second_line = schema.TextLine( title = u"Second Line" )
    ship_state = schema.TextLine( title = u"State ")
    ship_city = schema.TextLine( title = u"City" )
    ship_country = schema.TextLine( title = u"Country")
    ship_postal_code = schema.TextLine( title = u"Zip Code")

class IBillingAddress( IMemberSchema ):
    """ where to bill 
    """
    bill_first_line = schema.TextLine( title = u"First Line")
    bill_second_line = schema.TextLine( title = u"Second Line" )
    bill_state = schema.TextLine( title = u"State ")
    bill_city = schema.TextLine( title = u"City" )
    bill_country = schema.TextLine( title = u"Country")
    bill_postal_code = schema.TextLine( title = u"Zip Code")    

class IUserPaymentInformation( Interface ):
    """ A User's payment information to be optionally collected by the
    payment processor view.
    """

    name_on_card = schema.TextLine( title=u"Card Holder Name")
    phone_number = schema.TextLine( title=u"Phone Number")    
    # NOT STORED PERSISTENTLY
    credit_card_type = schema.Choice( title = u"Credit Card Type",
                                      values = ( u"Visa",
                                                 u"MasterCard",
                                                 u"Discover",
                                                 u"American Express" ) )
    
    credit_card = schema.TextLine( title = u"Credit Card Number")
    cc_expiration = schema.TextLine( title = u"Credit Card Expiration Date")
    cc_cvc = schema.TextLine(title = u"Credit Card Verfication Number")


    
class IPaymentTransaction( ILineItemContainer ):
    """  A Payment that's been applied
    """

    status = schema.Choice( title = u"Payment Status",
                            values = ( u"Accepted",
                                       u"Declined",
                                       u"Refunded" ) )
    
class IPersistentOptions( Interface ):
    """ interface
    """

#################################
# Orders

class IOrderManager( Interface ):
    """ persistent utility for storage and query of orders
    """

    def getOrdersByItem( item_id, **kw):
        """ retrieve all orders containing item_id
        """

    def getOrdersByUser( user_id, **kw):
        """ retrieve all orders for a given user id
        """

    def query( **kw ):
        """ query the orders
        """

    def get( order_id ):
        """ retrieve an order
        """

    def store( order ):
        """ save an order
        """

class IOrder( Interface ):

    shipping_address = schema.Object( IShippingAddress, required=False)
    billing_address  = schema.Object( IBillingAddress )
    shopping_cart = schema.Object( IShoppingCart )
    finance_state = schema.TextLine( title=u"Finance State", readonly=True)
    fufillment_state = schema.TextLine( title=u"Fufillment State", readonly=True)
    processor_order_id = schema.ASCIILine( title=u"Processor Order Id" )

class finance_states:

    REVIEWING = 'REVIEWING'
    CHARGEABLE = 'CHARGEABLE'
    CHARGING = 'CHARGING'
    CHARGED = 'CHARGED'
    REFUNDED = 'REFUNDED'
    PAYMENT_DECLINED = 'PAYMENT_DECLINED'
    CANCELLED = 'CANCELLED'
    CANCELLED_BY_PROCESSOR = 'CANCELLED_BY_PROCESSOR'

class fulfillment_states:

    NEW = 'NEW'
    PROCESSING = 'PROCESSING'
    DELIVERED = 'DELIVERED'
    WILL_NOT_DELIVER = 'WILL_NOT_DELIVER'
