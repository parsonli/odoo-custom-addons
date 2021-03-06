# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2018 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################

from odoo import models, api, http, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)


class website_sale_inquiry(http.Controller):

    @http.route(['/shop/enquiry/<model("product.template"):product>'],
                type='http', auth="public", website=True, sitemap=False)
    def make_inquiry(self, product, **post):
        """
        Create a Inquiry and reset website order.
        :return: Confirmation of Inquiry
        """
        lead = False
        if product:
            required_fields = ['name', 'email', 'mobile', 'message']
            if not set(required_fields).difference(post.keys()) and post.get('name', '') \
                and post.get('email', '') and post.get('mobile', '') and post.get('message', ''):
                lead = request.env['crm.lead'].sudo().create({
                    'name': 'Requirement for ' + str(product.display_name or ''),
                    'type': 'lead',
                    #'team_id': request.env.ref("crm_team").id,
                    'user_id': False,
                    'contact_name': post.get('name', ''),
                    'city': post.get('city', ''),
                    'partner_name': post.get('company_name', ''),
                    'country_id': post.get('country_id', False),
                    'state_id': post.get('state_id', False),
                    'street': post.get('street', ''),
                    'street2': post.get('street2', ''),
                    'zip': post.get('zip', ''),
                    'email_from': post.get('email', ''),
                    'description': post.get('message', ''),
                    'mobile': post.get('mobile', '')
                })

        if lead:
            # send product enquiry email to user
            template = False
            try:
                template = request.env.ref('enquiry_website_oin.product_enquiry_email', raise_if_not_found=False)
                if template:
                    assert template._name == 'mail.template'
                    template.sudo().send_mail(lead.id, force_send=True, raise_exception=True)
                    _logger.info("Product Enquiry email sent for user <%s> to <%s>", lead.contact_name, lead.email_from)
            except Exception as e:
                _logger.info("Something went wrong: <%s>", e)
        return request.render("enquiry_website_oin.enquiry_thankyou", {})


class WebsiteSale(WebsiteSale):

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        response = super(WebsiteSale, self).product(product, category, search, **kwargs)
        partner = request.env.user.sudo().partner_id
        countries = request.env['res.country'].sudo().search([])
        states = request.env['res.country.state'].sudo().search([])
        response.qcontext.update({'countries': countries,
                                  'states': states,
                                  'country': partner.country_id
                                  })
        return response
