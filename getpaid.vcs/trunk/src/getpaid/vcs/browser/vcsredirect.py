from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

import decimal,operator
import cgi
import cgitb; cgitb.enable()

from Products.PloneGetPaid.browser.checkout import CheckoutReviewAndPay, sanitize_custom_widgets, null_condition
from getpaid.core import interfaces, options
from getpaid.core.interfaces import IPaymentProcessor
from Products.PloneGetPaid.interfaces import IGetPaidManagementOptions
from zope import component
from zope import schema
from zope.component import getAdapter
from zope.formlib import form
from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile
from getpaid.wizard import Wizard, ListViewController, interfaces as wizard_interfaces
from getpaid.wizard import interfaces as wizard_interfaces
from getpaid.vcs import interfaces as vcs_interfaces

class VcsRedirect(BrowserView):
    template = ZopeTwoPageTemplateFile("templates/redirect.pt")

    def getQuerystring(self):
        form = self.request.form
        value = form.get('orderid')
        return value
    
    def returnForm(self):
        order_manager = component.getUtility(interfaces.IOrderManager)
        orderid = self.getQuerystring()
        if order_manager.isValid(orderid):
            order = order_manager.get(orderid)
        else:
            order = "invalid"
        price = order.getTotalPrice()
        orderId = order.order_id
        options = vcs_interfaces.IVcsStandardOptions(self.context)
        server_url = options.server_url
        urlArgs = dict(p1=options.pspid,
                       p2=orderId,
                       p3=options.orderdesc,
                       p4=price,
                       p5=options.currency,)
        formvals = {"p1": options.pspid,
                    "p2": orderId,
                    "p3": options.orderdesc,
                    "p4": price,
                    "p5": options.currency,
                    }
        _button_form = """<form style="display:inline;" action="https://www.vcs.co.za/vvonline/ccform.asp" method="post" id="vcs-button">
                            <input type="hidden" name="p1" value="%(p1)s" />
                            <input type="hidden" name="p2" value="%(p2)s" />
                            <input type="hidden" name="p3" value="%(p3)s" />
                            <input type="hidden" name="p4" value="%(p4)s" />
                            <input type="hidden" name="p5" value="%(p5)s" />
                            <input type="submit"
                                name="submit"
                                value="Proceed to Payment Page" />
                            </form>
                            """
        order.finance_workflow.fireTransition("authorize")
        component.getUtility(interfaces.IShoppingCartUtility).destroy(self.context)
        html = _button_form % formvals
        return html