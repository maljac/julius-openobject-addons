# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012 Julius Network Solutions SARL <contact@julius.fr>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################

from openerp.osv import fields, orm
from openerp.tools.translate import _

class account_invoice(orm.Model):
    _inherit = "account.invoice"

    def _emergency_line_to_create(self, cr, uid, line, context=None):
        if context is None:
            context = {}
        res = False
        if line.emergency_costs != 0 \
            and not line.emergency_costs_line_id:
            res = True
        return res

    def generate_emergency_costs_invoice_line(self, cr, uid, ids, context=None):
        invoice_line_obj = self.pool.get('account.invoice.line')
        sale_line_obj = self.pool.get('sale.order.line')
        data_obj = self.pool.get('ir.model.data')
        sale_obj = self.pool.get('sale.order')
        value = {}
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.state != 'draft':
                continue
            invoice_lines = invoice.invoice_line
            for invoice_line in invoice_lines:
                for sale_line in invoice_line.sale_lines:
                    if self._emergency_line_to_create(cr, uid,
                                                      sale_line,
                                                      context=context):
                        sale_order = sale_line.order_id
                        model, product_id = data_obj.get_object_reference(
                            cr, uid, 'emergency_costs', 'product_emergency_costs')
                        res = sale_line_obj.product_id_change(cr, uid, [],
                            pricelist=sale_order.pricelist_id.id,
                            product=product_id, qty=1,
                            partner_id=sale_order.partner_id.id,
                            lang=sale_order.partner_id.lang, update_tax=True,
                            date_order=sale_order.date_order,
                            context=context)
                        value = res.get('value')
                        if value:
                            value.update({
                                'invoice_id': invoice.id,
                                'product_id': product_id,
                                'price_unit': sale_line.emergency_costs,
                                'quantity': 1,
                                'invoice_line_tax_id': value.get('tax_id') \
                                     and [(6, 0, value.get('tax_id') or [])],
                            })
                        new_inv_line_id = invoice_line_obj.create(cr, uid, value, context=context)
                        sale_line_obj.write(cr, uid,
                            [sale_line.id],
                            {'emergency_costs_line_id' : new_inv_line_id},
                            context=context)
        return True

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: