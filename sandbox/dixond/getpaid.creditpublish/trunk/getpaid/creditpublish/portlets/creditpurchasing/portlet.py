__author__ = """Darryl Dixon <darryl.dixon@winterhouseconsulting.com>"""

from decimal import Decimal
from zope.interface import implements
from zope.component import getUtility, getAdapter, getMultiAdapter
from zope.formlib import form

from plone.app.portlets.portlets import base
from plone.portlets.interfaces import IPortletDataProvider
from plone.memoize.instance import memoize
from cornerstone.browser.base import RequestMixin
from DateTime.DateTime import DateTime

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName

from getpaid.core.interfaces import IBuyableContent, ILineItemFactory, IShoppingCartUtility, ITaxUtility
from getpaid.creditregistry.interfaces import ICreditRegistry

from getpaid.creditpublish import creditpublishMessageFactory as _
from getpaid.creditpublish.interfaces import IOneWeekPublishedCredit, IOneWeekCreditPublishedContent
from getpaid.creditpublish.portlets.interfaces import ICreditPurchasingPortlet

class Assignment(base.Assignment):
    implements(ICreditPurchasingPortlet)

    def __init__(self, representative_object=None):
        self.representative_object = representative_object

    @property
    def title(self):
        return _(u'getpaid.creditpurchasing', default=u'Credit Purchasing')
    
class Renderer(base.Renderer, RequestMixin):
    
    render = ViewPageTemplateFile('purchasing.pt')
    nameprefix = 'getpaid.creditpurchasing'

    def __init__(self, context, request, view, manager, data):
        super(Renderer, self).__init__(context, request, view, manager, data)
        # XXX FIX THIS UP SO THAT WE USE THE VIRTUAL ROOT
        self.sitepath = '/'
        self.pmt = getToolByName(self.context, 'portal_membership')
        self.pct = getToolByName(self.context, 'portal_catalog')
        self.put = getToolByName(self.context, 'portal_url')
        self.cr = getUtility(ICreditRegistry)

    def update(self):
        url = self.put()
        if self.request.get('REQUEST_METHOD', '') == 'POST':
            # Find out if this is really for us
            if self.formvalue('submitted') is not None:
                # Yep
                # Always deny anonymous checkout (it's insane for user credits)
                if getToolByName(self.context, 'portal_membership').isAnonymousUser():
                    url = "%s/%s" % (url, 'login_form')
                else:
                    # We'll give the option of sending the user back here after purchases of this type of credit
                    self.sessionset(IOneWeekPublishedCredit.__identifier__, self.request['ACTUAL_URL'])
                    weeks = self.formvalue('weeks')
                    credititem = self.formvalue('credititem')
                    credititem = self.pct.unrestrictedSearchResults(UID=credititem)
                    if credititem:
                        credititem = credititem[0].getObject()
                        # create a line item and add it to the cart
                        item_factory = getMultiAdapter((self.getCart(), credititem), ILineItemFactory)
                        # check quantity from request
                        item_factory.create(quantity=weeks)
                    url += '/@@getpaid-checkout-wizard'
                return self.request.RESPONSE.redirect(url, status=302)

    def getCart(self):
        cart_manager = getUtility(IShoppingCartUtility)
        return cart_manager.get(self.context, create=True)

    @property
    def available(self):
        if not self.pmt.isAnonymousUser():
            if self.representative_object is not None:
                return True
        return False

    def formname(self):
        return "%s.form" % self.nameprefix

    def current_credit(self):
        buyable = getAdapter(self.representative_object, IBuyableContent)
        raw_price = buyable.price
        member = self.pmt.getAuthenticatedMember()
        return (self.cr.queryCredit(member.getId(), IOneWeekPublishedCredit.__identifier__) / Decimal('%0.2f' % raw_price))

    def cashvalue(self):
        tax = getUtility(ITaxUtility)
        member = self.pmt.getAuthenticatedMember()
        cred = self.cr.queryCredit(member.getId(), IOneWeekPublishedCredit.__identifier__)
        return '$%0.2f' % float(cred + tax.getTaxOnSum(cred))

    def weeks_options(self):
        return range(1, 53)

    @property
    def representative_object(self):
        ro = self.pct.unrestrictedSearchResults(UID=self.data.representative_object)[:1]
        if ro:
            return ro[0].getObject()
        else:
            return None

    @property
    def credit_price(self):
        """Return a dict containing the price of the credit item and the tax applicable and a 'tax string'
        """
        buyable = getAdapter(self.representative_object, IBuyableContent)
        raw_price = buyable.price
        class fakeorder(object):
            def __init__(self, buyable):
                self.buyable = buyable
            def getSubTotalPrice(self):
                return self.buyable.price
            def getShippingCost(self):
                return 0
        tax = getUtility(ITaxUtility).getTaxes(fakeorder(buyable))
        return {'price' : '%.2f' % (raw_price + float(sum([x['value'] for x in tax]))), 'taxes' : [x['name'] for x in tax]}

class AddForm(base.AddForm):
    form_fields = form.Fields(ICreditPurchasingPortlet)
    label = _(u"Add Credit Purchasing Portlet")
    description = _(u"This portlet displays purchasable credits")

    # This method must be implemented to actually construct the object.
    # The 'data' parameter is a dictionary, containing the values entered
    # by the user.

    def create(self, data):
        assignment = Assignment()
        form.applyChanges(assignment, self.form_fields, data)
        return assignment

class EditForm(base.EditForm):
    form_fields = form.Fields(ICreditPurchasingPortlet)
    label = _(u"Edit Credit Purchasing Portlet")
    description = _(u"This portlet displays purchasable credits")
