"""
collective.z3cform.wizard based checkout wizard
"""

__version__ = "$Revision$"
# $Id$
# $URL$

import time
import types
import hashlib
import cPickle
import ZTUtils

from zope import component, exceptions, interface, schema, viewlet

from zope.schema.vocabulary import SimpleVocabulary

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.Five.viewlet.manager import ViewletManagerBase
from Products.Five.viewlet.viewlet import ViewletBase

from Products.CMFCore.utils import getToolByName

from z3c.form import button, field, group, form
from z3c.form.interfaces import IFormLayer, IDisplayForm, INPUT_MODE, DISPLAY_MODE, HIDDEN_MODE
from z3c.form.browser import radio

from collective.z3cform.datetimewidget import MonthYearFieldWidget

# @view.memoize cache values for the lifespan of request
from plone.memoize import view 

from getpaid.core import interfaces
from getpaid.core.order import Order
from getpaid.core.interfaces import workflow_states as wf

from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from Products.PloneGetPaid.browser.interfaces import IDontShowGetPaidPortlets
from Products.PloneGetPaid import _

from collective.z3cform.wizard.interfaces import IWizard, IStep
from collective.z3cform.wizard import wizard, utils


class ICheckoutContinuationKey(interface.Interface):
    """ Adapts Order to Checkout Wizard Continuation Key """


class CheckoutContinuationKeyAdapter(object):
    """ Adapts Order to Checkout Wizard Continuation Key """

    interface.implements(ICheckoutContinuationKey)

    key = None

    def __repr__(self):
        if self.key is not None:
            return self.key
        return super(CheckoutContinuationKeyAdapter, self).__repr__()

    def __init__(self, order):
        key = hashlib.md5()
        key.update(str(order.order_id))
        key.update(str(order.processor_order_id))
        key.update(str(order.creation_date))
        self.key = key.hexdigest()


class IPaymentProcessorButtonManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for rendering payment buttons for payment processors """


class IBeforePaymentMethodsViewletManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for plugins to add messages before payment method step details """


class IAfterPaymentMethodsViewletManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for plugins to add messages after payment method step details """


class IBeforeConfirmationViewletManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for plugins to add messages before confirmation step details """


class IAfterConfirmationViewletManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for plugins to add messages after confirmation step details """


class CheckoutWizardViewletBase(ViewletBase):
    """ Checkout Wizard Payment button base """

    def __init__(self, context, request, view, manager):
        self.wizard = hasattr(view, 'wizard') and view.wizard or view
        super(CheckoutWizardViewletBase, self).__init__(context, request, view, manager)


class PaymentProcessorButtonManager(ViewletManagerBase):
    """ Viewlet manager for rendering payment buttons for payment processors """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def filter(self, viewlets):
        viewlets = super(PaymentProcessorButtonManager, self).filter(viewlets)
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        results = []
        for name, viewlet in viewlets:
            if name in IGetPaidManagementOptions(portal).payment_processors:
                results.append((name, viewlet))
        return results

    def render(self):
        return "\n".join([b.render().strip() or "" for b in self.viewlets]).strip()


class BeforePaymentMethodsViewletManager(ViewletManagerBase):
    """ Viewlet manager for plugins to add messages before payment method step details """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def render(self):
        return "\n".join([v.render().strip() or "" for v in self.viewlets]).strip()


class AfterPaymentMethodsViewletManager(ViewletManagerBase):
    """ Viewlet manager for plugins to add messages after payment method step details """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def render(self):
        return "\n".join([v.render().strip() or "" for v in self.viewlets]).strip()


class BeforeConfirmationViewletManager(ViewletManagerBase):
    """ Viewlet manager for plugins to add messages before confirmation step details """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def render(self):
        return "\n".join([v.render().strip() or "" for v in self.viewlets]).strip()


class AfterConfirmationViewletManager(ViewletManagerBase):
    """ Viewlet manager for plugins to add messages after confirmation step details """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def render(self):
        return "\n".join([v.render().strip() or "" for v in self.viewlets]).strip()


class ICheckoutWizardStepDisplayViewletManager(viewlet.interfaces.IViewletManager):
    """ Viewlet manager for rendering results from checkout wizard steps """


class CheckoutWizardStepDisplayViewletManager(ViewletManagerBase):
    """ Viewlet manager for rendering results from checkout wizard steps """

    def sort(self, viewlets):
        """ sort by weight """
        return sorted(viewlets, lambda x,y: cmp(int(getattr(x[1], 'weight', 100)), int(getattr(y[1], 'weight', 100))))

    def render(self):
        return "\n".join([v.render().strip() or "" for v in self.viewlets]).strip()


class SchemaGroup(group.Group):
    """ z3c.form.group, which extracts its fields from getpaid FormSchemas """
    label = _(u"Abstract schema group")
    section = None # see getpaid.core.interfaces.IFormSchemas for options

    def __init__(self, context, request, parentForm):
        assert self.section is not None,\
            "Inherit SchemaGroup and overwrite section with getpaid schema section."
        self.prefix = self.section
        schemas = component.getUtility(interfaces.IFormSchemas)
        schema_fields = []

        # FIXME: collective.z3cform.wizard doesn't support interface bound fields
        # and therefore, we must clone fields and detach the clones form interfaces:
        for name, iface_field in schema.getFieldsInOrder(schemas.getInterface(self.section)):
            schema_field = iface_field.__class__.__new__(iface_field.__class__)
            schema_field.__dict__.update(iface_field.__dict__)
            schema_field.interface = None
            schema_fields.append(schema_field)

        self.fields = field.Fields(*schema_fields)
        super(SchemaGroup, self).__init__(context, request, parentForm)
   
    def getContent(self):
        return self.parentForm.getContent()


class DifferentEmail(schema.interfaces.ValidationError):
    __doc__ = _(u"Re-entered email address did not match the first one.")


class ContactGroup(SchemaGroup):
    label = _(u"Contact information")
    section = 'contact_information'

    def __init__(self, context, request, parentForm):
        super(ContactGroup, self).__init__(context, request, parentForm)
        if "email" in self.fields.keys() and self.parentForm.mode == INPUT_MODE:
            verify_email = self.fields["email"].field.__class__.__new__(self.fields["email"].field.__class__)
            verify_email.__dict__.update(self.fields["email"].field.__dict__)
            verify_email.interface = None
            verify_email.__name__ = "verify_email"
            verify_email.title = _(u"Verify E-mail address")
            verify_email.description = _(u"Please, re-enter your e-mail address")
            self.fields += field.Fields(verify_email)

    def updateWidgets(self):
        if "verify_email" in self.fields.keys() and self.parentForm.mode == DISPLAY_MODE:
            self.fields["verify_email"].mode = HIDDEN_MODE
        super(ContactGroup, self).updateWidgets()
        if "verify_email" in self.widgets.keys():
            self.widgets["verify_email"].field.constraint = lambda x: self.verifyEmail(x)

    def verifyEmail(self, email):
        if "email" in self.widgets.keys():
            if email != self.widgets["email"].extract():
                raise DifferentEmail
        return True


class BillingGroup(SchemaGroup):
    label = _(u"Billing information")
    section = 'billing_address'


class ShippingGroup(SchemaGroup):
    label = _(u"Shipping information")
    section = 'shipping_address'


class PaymentGroup(SchemaGroup):
    label = _(u"Payment information")
    section = 'payment'

    def __init__(self, *args):
        super(PaymentGroup, self).__init__(*args)
        self.fields["cc_expiration"].widgetFactory = MonthYearFieldWidget


class Customer(wizard.GroupStep):
    prefix = 'details'
    label  = _(u"Enter Customer Details")
    description = _(u"Please, enter the requested customer information for your order.")
    weight = 20

    groups = None
    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-customer.pt")

    @property
    def available(self):
        return super(Customer, self).available \
            and not self.wizard.isOrderAvailable
    
    def __init__(self, context, request, wizard):
        """ Filter required FormSchema sections """
        # Find the cart
        cart = wizard.isCartAvailable and wizard._cart \
            or wizard.isOrderAvailable and wizard._order.shopping_cart \
            or None
        # No groups when cart is empty
        if cart is None:
            self.groups = ()
        # Include shipping information only, when cart
        # contains shippable items
        elif len([i for i in cart.values() \
                  if interfaces.IShippableLineItem.providedBy(i)]):
            self.groups = (ContactGroup, ShippingGroup)
            # self.groups = (ContactGroup, BillingGroup, ShippingGroup)
        # By default, include
        else:
            self.groups = (ContactGroup,)
            # self.groups = (ContactGroup, BillingGroup)
        super(Customer, self).__init__(context, request, wizard)


class Review(wizard.Step):
    prefix = 'review'
    label  = _(u"Review Order")
    description = _(u"Please, review your order information before continuing the checkout.")
    weight = 40

    template = ViewPageTemplateFile("templates/checkout-wizard-step-review.pt")

    @property
    def available(self):
        return super(Review, self).available \
            and not self.wizard.isOrderAvailable

    def applyChanges(self, data):
        super(Review, self).applyChanges(data)
        # Now, when all order details should be collected (and only processor specific 
        # steps left), create an order and attach it to the session
        if not self.wizard.isOrderAvailable \
                and "form.buttons.back" not in self.request.form.keys():
            self.wizard.session['order_id'] = self.wizard._createOrder()
            self.wizard.session['key'] = str(ICheckoutContinuationKey(self.wizard._order))
            self.wizard.sync()


class Method(wizard.Step):
    prefix = 'method'
    label  = _(u"Select Payment Method")
    description = _(u"Please, select a method to pay your order.")
    weight = 60

    fields = field.Fields(
       schema.Choice(__name__='processor_id', title=_(u"Available payment methods"),
                     values=[], required=True))
    template = ViewPageTemplateFile("templates/checkout-wizard-step-method.pt")

    @property
    def available(self):
        return self.wizard.isOrderAvailable \
            and self.wizard._order.finance_state == None

    def update(self):
        """ Setup widget for stepful payment processors, when processor spesific steps found """
        # FIXME: We cannot use IContextSourceBinder, because its context
        # would be wizard's data container (a dict from session) with no
        # way to get the wizard object.
        sm = component.getSiteManager()
        descriptions = {} # Processor's description should be stored as its registration info
        for registration in [r for r in sm.registeredUtilities() if r.name and r.info]:
            descriptions[registration.name] = registration.info
        stepful_processors = [SimpleVocabulary.createTerm(name, name, descriptions.get(name, _(name))) \
                                   for name in self.wizard._stepful_processors]
        if stepful_processors:
            self.fields["processor_id"].field.vocabulary = SimpleVocabulary(stepful_processors)
            self.fields["processor_id"].widgetFactory = radio.RadioFieldWidget
        else:
            self.fields["processor_id"].mode = HIDDEN_MODE
        super(Method, self).update()

    @property
    def order_id(self):
        return self.wizard._order.order_id


class Payment(wizard.GroupStep):
    """ A default payment information step, must be explicitly included by payment processor """
    prefix = 'payment'
    label  = _(u"Payment Details")
    description = _(u"Please, enter your payment information for the order.")
    weight = 70

    groups = (PaymentGroup,)
    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-payment.pt")

    @property
    def available(self):
        return super(Payment, self).available \
            and self.wizard.isOrderAvailable \
            and self.wizard._order.finance_state == None

    @property
    def order_id(self):
        return self.wizard._order.order_id


class Confirmation(wizard.Step):
    """ Order confirmation view """
    prefix = 'confirmation'
    label  = _(u"Order Confirmation")
    description = _(u"Thank you for your order.")
    weight = 80

    fields = field.Fields()
    template = ViewPageTemplateFile("templates/checkout-wizard-step-confirmation.pt")

    @property
    def available(self):
        return super(Confirmation, self).available \
            and self.wizard.isOrderAvailable

    @property
    def order_date(self):
        util = getToolByName(self.context, "translation_service")
        return util.ulocalized_time(time.mktime(self.wizard._order.creation_date.timetuple()),
                                    False, None, context=self.context,
                                    domain='plonelocales', request=self.request)
    @property
    def order_id(self):
        return self.wizard._order.order_id

    @property
    def finance_state(self):
        return self.wizard._order.finance_state

    @property
    def fulfillment_state(self):
        return self.wizard._order.fulfillment_state

    def update(self):
        # For not yet authorized order
        if self.wizard._order.finance_state == None \
                and self.wizard._authorizeOrder() != interfaces.keys.results_success:
            utils = getToolByName(self.context, 'plone_utils')
            utils.addPortalMessage(_(u"Your payment information couldn't be verified."))
            self.wizard.jump(self.wizard.currentIndex - 1)
        # For orders in other state
        else:
            super(Confirmation, self).update()


class PreviousStepsDisplayProvider(object):
    """ Content provider for rendering previous steps as display forms """

    previous = []

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.wizard = hasattr(view, 'wizard') and view.wizard or view

    def update(self):
        # Include all previous steps, whose data is found found on the session
        self.previous = [s for s in self.wizard.activeSteps[:self.wizard.currentIndex]
                         if self.wizard.session.get(s.prefix, None) or None is not None]
        for previous in self.previous:
            interface.alsoProvides(previous, IDisplayForm)
            previous.mode = DISPLAY_MODE
            previous.ignoreRequest = True
            previous.update()

    def render(self):
        return "\n".join([p.render().strip() for p in self.previous]).strip()


class ITransactionReferenceNumberProvider(interface.Interface):
    """Transaction reference number provider for orders """

    def new(self, order=None):
        """ Return new unused transaction reference number for an order """
        raise NotImplementedError


class ICheckoutWizard(IWizard):
    """ Marker interface for wizard to adapt steps for it """


class CheckoutWizard(wizard.Wizard):
    """ Payment checkout wizard """
    interface.implements(ICheckoutWizard, IDontShowGetPaidPortlets)

    buttons = wizard.Wizard.buttons.select('continue', 'back')
    handlers = wizard.Wizard.handlers.copy()

    label = _(u"Checkout")

    # the overwritten collective.z3cform.wizard is found at self.index
    template = ViewPageTemplateFile("templates/checkout-wizard.pt")

    def __init__(self, context, request):
        super(CheckoutWizard, self).__init__(context, request)
        # Add IFormLayer for request to support z3c.form
        interface.alsoProvides(self.request, IFormLayer)

        # Request login, when anonymous user and anonymous checkouts has not been allowed
        mtool = getToolByName(self.context, 'portal_membership')
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        if mtool.isAnonymousUser() and not IGetPaidManagementOptions(site).allow_anonymous_checkout:
            self.request.response.redirect('login_form?came_from=@@checkout')

        # Redirect http:// to https:// when required
        url = self.request.getURL()
        if IGetPaidManagementOptions(site).use_ssl_for_checkout and not "https://" in url:
            url = url.replace("http://", "https://")
            querystring = ZTUtils.make_query(self.request.form)
            self.request.response.redirect('%s?%s' % (url, querystring))

        # Configure z3cform.wizard's default buttons
        self.buttons["back"].title = _(u"Back")
        self.buttons["back"].condition = lambda form: form.isBackAvailable
        self.buttons["continue"].title = _(u"Continue")
        self.buttons["continue"].condition = lambda form: form.isContinueAvailable

    def update(self):
        """ See: collective.z3cform.wizard.Wizard.update() """
        # Had to overwrite whole update to get more control on 
        # initialization of steps, particularly, to enable
        # declarative configuration of steps via zcml/adapters

        # Initialize session
        sessionKey = self.sessionKey
        if not self.request.SESSION.has_key(sessionKey):
            self.request.SESSION[sessionKey] = {}

        # Reset session if we came from a URL different from that of the wizard,
        # unless it's the URL that's used during z3cform inline validation.
        referer = self.request.environ.get('HTTP_REFERER', "").replace("@@", "")
        url = self.request.get('ACTUAL_URL', "").replace("@@", "")
        if not self.isOrderAvailable and referer.startswith('http') \
                and 'kss_z3cform_inline_validation' not in url \
                and not referer.endswith('/shopping-cart') \
                and not utils.location_is_equal(url, referer):
            self.request.SESSION[sessionKey] = {}
        self.session = self.request.SESSION[sessionKey]

        # Get all payment processors (to filter possible processors steps)
        # Query and initialize steps, include processor step if processor selected
        self.activeSteps = []
        for name, step in component.getAdapters((self.context, self.request, self), IStep):
            if not [p for p in self._processor_names if name.startswith(p)] \
                    or (self._selected_processor_id and name.startswith(self._selected_processor_id)):
                step.__name__ = name
                self.activeSteps.append(step)
        self.activeSteps.sort(lambda x,y: cmp(int(getattr(x, 'weight', 100)), int(getattr(y, 'weight', 100))))

        # Selection of the active step:
        # a) If paid order exist, jump always to the final step
        if self.isOrderAvailable \
                and self._order.finance_state not in [None, wf.order.finance.REVIEWING]:
            self.updateCurrentStep(len(self.activeSteps) - 1)
        # b) othewise, look for explicit (available) step from request
        elif 'step' in self.request.form:
            try:
                self.jump(max(min(int(self.request.form['step']), len(self.activeSteps) - 1), 0))
            except ValueError:
                pass
        # c) or let the wizard continue as usual (which may also lead to the final step)
        if not self.currentStep:
            available = [s.available for s in self.activeSteps]
            try:
                first = available.index(True)
            except ValueError:
                first = 0
            self.updateCurrentStep(self.session.setdefault('step', first))
        # Perform regular z3c.form update cycle
        self.updateActions()
        self.actions.execute()
        self.updateWidgets()

    def render(self):
        raw = super(CheckoutWizard, self).render()
        # Reset the session after the final step has been rendered
        if self.currentStep == self.activeSteps[-1]:
            self._resetSession()
        return raw

    @button.buttonAndHandler(_(u"Cancel order"), name="cancel",
                             condition=lambda form: not form.onLastStep)
    def handleCancel(self, action):
        self._cancelOrder()
        self._destroyCart()
        self._resetSession()
        utils = getToolByName(self.context, 'plone_utils')
        utils.addPortalMessage(_(u"Your order has been cancelled."))
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        # FIXME: What'd be the most proper action after cancelling order?
        self.request.response.redirect(self.refererURL)

    @property
    def onLastStep(self):
        return self.currentIndex == len(self.activeSteps) - 1

    @property
    def isBackAvailable(self):
        return not self.onFirstStep \
            and self.currentIndex is not None \
            and self.activeSteps[self.currentIndex - 1].available
    
    @property
    def isContinueAvailable(self):
        return not self.onLastStep \
            and (not self.isOrderAvailable or self.areStepfulProcessorsAvailable)

    @property
    def isCartAvailable(self):
        return self._cart and True or False

    @property
    def isOrderAvailable(self):
        return self._order and True or False

    @property
    def areStepfulProcessorsAvailable(self):
        return self._stepful_processors and True or False

    @property
    def isVerifiedCheckoutContinuation(self):
        if self.isOrderAvailable:
            key = str(ICheckoutContinuationKey(self._order))
            if self.request.form.has_key("key"):
                return self.request.form.get("key") == key
            elif hasattr(self, "session") and self.session.get("key", None):
                return str(self.session.get("key")) == key
        return False

    @property
    def canPaymentButtonsBeShown(self):
        finance_state = self.isOrderAvailable \
            and self._order.finance_workflow.state().getState() or None
        return self.isOrderAvailable and not self.isBackAvailable \
            and finance_state is None

    @property
    def refererURL(self):
        if self.session.has_key("cancel_url"):
            return self.session.get("cancel_url")
        portal_url = getToolByName(self.context, "portal_url")
        site = portal_url.getPortalObject()
        referer = self.request.get('GETPAID_REFERER', self.request.environ.get('HTTP_REFERER', None))
        return referer or site.absolute_url()

    @property
    def _cart(self):
        manager = component.getUtility( interfaces.IShoppingCartUtility )
        return manager.get(self.context, create=False) or None

    @property
    def _order(self):
        manager = component.getUtility(interfaces.IOrderManager)
        order_id = hasattr(self, "session") and self.session.get("order_id", None) \
            or self.request.form.get("order_id", None)
        order = order_id and order_id in manager and manager.get(order_id) or None
        # Save the order to the session so that it would be possible
        # to finish the checkout also with broken session.
        if order is not None and hasattr(self, "session") \
               and self.session.get("order_id", None) is None:
            self.session["order_id"] = order_id
            self.sync()
        return order

    @property
    def _selected_processor_id(self):
        """ selected payment processor, when selected """
        return self.request.form.get('method.widgets.processor_id', [None])[0] \
            or self.session.has_key('method') and self.session['method'].get('processor_id', None) or None

    @property
    @view.memoize
    def _processor_names(self):
        """ selected payment processor, when selected """
        processor_names = [processor.value for processor in
                           component.getUtility(schema.interfaces.IVocabularyFactory,
                                                "getpaid.payment_methods")(self.context)]
        # Append also uninstalled processors, since their adapters are registered anyway
        for plugin_id, plugin_manager in component.getAdapters((self.context,), interfaces.IPluginManager):
            if plugin_id not in processor_names:
                processor_names.append(plugin_id)
        return processor_names

    @property
    @view.memoize
    def _stepful_processors(self):
        site = getToolByName(self.context, 'portal_url').getPortalObject()
        enabled_processors = IGetPaidManagementOptions(site).payment_processors
        return [processor for processor in enabled_processors \
                    if component.queryMultiAdapter((self.context, self.request, self), IStep, name=processor)]

    def _resetSession(self):
        self.request.SESSION[self.sessionKey] = {}
        self.sync()

    def _createOrder(self):
        # FIXME: currently, this is oversimplication of order creation process and
        # doesn't include shipping or any other "special" cases
        order = Order()
        
        mtool = getToolByName(self.context, "portal_membership")
        if mtool.isAnonymousUser():
            order.user_id = "anonymous"
        else:
            order.user_id = mtool.getAuthenticatedMember().getId()

        # Fill in the order by searching the wizard's session for
        # field names defined by getpaid form schemas.
        schemas = component.getUtility(interfaces.IFormSchemas)
        for section in ("billing_address", "shipping_address", "contact_information"):
            bag = schemas.getBagClass(section)()
            for field_name, field in schema.getFieldsInOrder(bag.schema):
                for step in self.session.keys():
                    if type(self.session[step]) is types.DictType \
                            and self.session[step].has_key(field_name):
                        setattr(bag, field_name, self.session[step][field_name])
            setattr(order, section, bag)
        order.name_on_card = order.billing_address.bill_name
        order.bill_phone_number = order.contact_information.phone_number

        # Shopping cart is attached to the session, but we want to
        # switch the storage to the persistent zodb, we pickle to get a
        # clean copy to store.
        order.shopping_cart = cPickle.loads(cPickle.dumps(self._cart))

        # Store the order
        manager = component.getUtility(interfaces.IOrderManager)
        while True:
            order.order_id = manager.newOrderId()
            try:
                manager.store(order)
                break
            except exceptions.DuplicationError:
                # the id was taken, try again
                pass

        sm = component.getSiteManager()
        trans_id = [u[1] for u in sm.getUtilitiesFor(ITransactionReferenceNumberProvider)]
        if trans_id:
            # Orders do have badly documented user_payment_info_trans_id property,
            # which has even its own setter. See: getpaid.core.order
            order.setOrderTransId(trans_id[0].new(order))

        self._destroyCart()
        return order.order_id
    
    def _authorizeOrder(self):
        """ Simple authorization for onsite (stepful) payment processors """

        order = self._order
        processor_id = self._selected_processor_id
        processor = component.getUtility(interfaces.IPaymentProcessor, name=processor_id)

        # Fill in the payment information
        schemas = component.getUtility(interfaces.IFormSchemas)
        payment_information = schemas.getBagClass("payment")(self.session)
        for field_name, field in schema.getFieldsInOrder(payment_information.schema):
            for step in self.session.keys():
                if type(self.session[step]) is types.DictType \
                        and self.session[step].has_key(field_name):
                    setattr(payment_information, field_name, self.session[step][field_name])

        # FIXME: This doesn't currently store anything from payment_information
        # to order, if processor doesn't do it
        if processor.authorize(order, payment_information) == interfaces.keys.results_success:
            order.processor_id = processor_id
            if order.fulfillment_state == None:
                order.fulfillment_workflow.fireTransition("create", u("Order created by wizard."))

            # FIXME: This should happen automatically (via subscriber)
            # when order's "create" transition occurs...
            for item in order.shopping_cart.values():
                if item.fulfillment_state is None:
                    item.fulfillment_workflow.fireTransition("create", _(u"Order created by wizard."))

            if order.finance_state == None:
                order.finance_workflow.fireTransition('create', _(u"Order created by wizard."))
            # I wonder if it's OK to fire "authorize" here, because it also
            # fires "charge", but since there's no GUI for manually "charge",
            # I'll leave it here for now...
            if order.finance_state == wf.order.finance.REVIEWING:
                order.finance_workflow.fireTransition("authorize",
                                                      _(u"Order self-authorized without by wizard."))

            return interfaces.keys.results_success
        else:
            return False

    def _cancelOrder(self):
        if self.isOrderAvailable:
            order = self._order

            if not hasattr(order, "processor_id"):
                order.processor_id = None

            if order.finance_state is None:
                order.finance_workflow.fireTransition("create",
                                                      _(u"Order cancelled by customer."))
            if order.finance_state is wf.order.finance.REVIEWING:
                order.finance_workflow.fireTransition("reviewing-declined",
                                                      _(u"Order cancelled by customer."))
            if order.finance_state is wf.order.finance.PAYMENT_DECLINED:
                order.finance_workflow.fireTransition("cancel-declined",
                                                      _(u"Order cancelled by customer."))

            if order.fulfillment_state is None:
                order.fulfillment_workflow.fireTransition("create",
                                                          _(u"Order cancelled by customer."))
            if order.fulfillment_state is wf.order.fulfillment.NEW:
                order.fulfillment_workflow.fireTransition("cancel-new-order",
                                                          _(u"Order cancelled by customer."))
                
            for item in order.shopping_cart.values():
                if item.fulfillment_state is None:
                    item.fulfillment_workflow.fireTransition("create",
                                                             _(u"Order cancelled by customer."))
                if item.fulfillment_state is wf.item.NEW:
                    item.fulfillment_workflow.fireTransition("cancel",
                                                             _(u"Order cancelled by customer."))

    def _destroyCart(self):
        component.getUtility(interfaces.IShoppingCartUtility).destroy(self.context)
