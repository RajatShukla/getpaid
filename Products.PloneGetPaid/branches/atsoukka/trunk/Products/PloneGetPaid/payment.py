from zope import component
from zope.interface import implements
from getpaid.core.payment import CreditCardTypeEnumerator
from getpaid.core.interfaces import ICreditCardTypeEnumerator, IPaymentProcessor
from interfaces import IGetPaidManagementOptions
from Products.CMFCore.utils import getToolByName

class CreditCardTypeEnumerator(CreditCardTypeEnumerator):
    implements(ICreditCardTypeEnumerator)

    def __init__(self, context):
        self.context = context

    def acceptedCreditCardTypes(self):
        # Get the configured values

        # FIXME: We cannot use self.context to locate Plone Site object,
        # because self.context on collective.z3cform.wizard.Step contains
        # wizard's data container (a dict from session).
        site = component.getSiteManager()
        portal = getToolByName(site, 'portal_url').getPortalObject()

        options = IGetPaidManagementOptions(portal)

        processors = [component.getUtility(IPaymentProcessor, name=processor)
                      for processor in options.payment_processors]

        accepted_credit_cards = {}
        for processor in [p for p in processors if hasattr(p, 'accepted_credit_cards')]:
            for name in getattr(processor, 'accepted_credit_cards'):
                accepted_credit_cards[name] = True

        return accepted_credit_cards.keys()
