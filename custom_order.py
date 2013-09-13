import time
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import openerp
from openerp import pooler, tools
from openerp.osv import osv, fields
from openerp.tools.translate import _
from connect_order import connect, connect_write
import fcntl
import sys

class sale_order_category(osv.osv):
    """ Category of Medical Order """
    _name = "sale.order.category"
    _description = "Medical Order Category"
    _columns = {
        'name': fields.char('Category Name', size=64, required=True),
        'description': fields.char('Description', size=64, required=True),
    }
    _sql_constraints = [
        ('name', 'unique(name)', 'The name of the category must be unique')
    ]
    _order = 'name asc'



sale_order_category()


class sale_order_custom (osv.osv):

    _name = "sale.order"
    _inherit = "sale.order"
    _description= "Medical orders"
    _columns = {
        'order_ref' : fields.char ('Prescription Number', size=50, required=True),
        'order_type' : fields.many2one('sale.order.category', 'Type', required=True, readonly=True), 
        'ordered_by' : fields.char ('Ordered By', size=50),
        'patient_ref' : fields.char ('Patient Number', size=50),
        'order_instructions' : fields.char ('Instructions', size=50),
        'order_payment_date' : fields.date ('Payment date'),
        'payment_notes' : fields.char ('Notes', size=50),
        'order_state': fields.selection([
            ('draft', 'Draft Order'),
            ('paid', 'Order Paid'),
            ('invoiced', 'Invoiced'),
            ('cleared', 'Cleared'),
            ('cancel', 'Cancelled'),
             ], 'Status', readonly=True, track_visibility='onchange',
            help="Gives the status of the order. \nThe draft status is automatically set when a order is created. \nThe 'Paid' status is set when the order is paid for. \nThe 'Cancel' status is set when the order is cancelled.", select=True),

        'for_synchronization' : fields.boolean ('For Synchronization'),

         'prescription_state': fields.selection([
            ('modified', 'Modified'),
            ('partial_dispense', 'Partial Dispense'),
            ('dispensed', 'Dispensed'),])
           
            }
       
sale_order_custom ()



class sale_order_prescription(osv.osv):

    _name = "sale.order"
    _inherit = "sale.order"
    _description= "Prescription"
    _track = {
        'state': {
            'sale.prescription_paid': lambda self, cr, uid, obj, ctx=None: obj['prescriptionState'] in ['paid'],
            'sale.prescription_changed': lambda self, cr, uid, obj, ctx=None: obj['prescriptionState'] in ['modified'],
            'sale.prescription_partail_dispense': lambda self, cr, uid, obj, ctx=None: obj['prescriptionState'] in ['partial_dispense'],
            'sale.prescription_dispensed': lambda self, cr, uid, obj, ctx=None: obj['state'] in ['dispensed']
        },
      } 

    def copy(self, cr, uid, id, default=None, context=None):
        raise osv.except_osv(_('Restricted!!!'),_('Duplication could cause database desynchronization'))

    def create(self, cr, uid, vals, context={}):
        openmrs_object = self.pool.get('openmrs.order.connect')
        recId = openmrs_object.search(cr, uid, [], offset=0, limit=1, order=None, context=None, count=False)[0]
        username = openmrs_object.browse(cr, uid, recId, context={}).username
        ip_address = openmrs_object.browse(cr, uid, recId, context={}).ip_address
        port = openmrs_object.browse(cr, uid, recId, context={}).port
        password = openmrs_object.browse(cr, uid, recId, context={}).password
        database = openmrs_object.browse(cr, uid, recId, context={}).database
        identifier_type = openmrs_object.browse(cr, uid, recId, context={}).identifier_type
        update_type='order'; 
        res = super(sale_order_prescription, self).create(cr, uid, vals)

        values = {}
	values['order_ref'] = self.browse(cr, uid, rec, context={}).state_id.order_ref
	values['ordered_by'] = self.browse(cr, uid, rec, context={}).ordered_by
	values['patient_ref'] = self.browse(cr, uid, rec, context={}).patient_ref
	values['order_instructions'] = self.browse(cr, uid, rec, context={}).order_instructions
	values['order_state'] = self.browse(cr, uid, rec, context={}).order_state
	values['partner_invoice_id'] = self.browse(cr, uid, rec, context={}).partner_invoice_id
	values['order_type'] = self.browse(cr, uid, rec, context={}).order_type
	values['order_payment_date'] = self.browse(cr, uid, rec, context={}).order_payment_date
	values['payment_notes'] = self.browse(cr, uid, rec, context={}).payment_notes
            
        
        for item in values:
            if (values[item] is None) or (values[item] is False):
                values[item] = " "
        #raise osv.except_osv(_('Expecting an Agency Code'),_('IP adress is: %s' % values))
        try:
            id_openmrs = connect(ip_address, port, username, password, database, values, identifier_type,update_type)
            super(sale_order_prescription, self).write(cr, uid, res, {'openmrs_number': id_openmrs}, context={})
            super(sale_order_prescription, self).write(cr, uid, res, {'for_synchronization': False}, context={})
        except:
            super(sale_order_prescription, self).write(cr, uid, res, {'for_synchronization': True}, context={})
        return res

    def write(self, cr, uid, ids, vals, context={}):
        res = super(sale_order_prescription, self).write(cr, uid, ids, vals)
        openmrs_object = self.pool.get('openmrs.order.connect')
        recId = openmrs_object.search(cr, uid, [], offset=0, limit=1, order=None, context=None, count=False)[0]
        username = openmrs_object.browse(cr, uid, recId, context={}).username
        ip_address = openmrs_object.browse(cr, uid, recId, context={}).ip_address
        port = openmrs_object.browse(cr, uid, recId, context={}).port
        password = openmrs_object.browse(cr, uid, recId, context={}).password
        database = openmrs_object.browse(cr, uid, recId, context={}).database
        identifier_type = openmrs_object.browse(cr, uid, recId, context={}).identifier_type
        update_type='order';
        for rec in ids:
            values ={}
	    values['order_ref'] = self.browse(cr, uid, rec, context={}).state_id.order_ref
	    values['ordered_by'] = self.browse(cr, uid, rec, context={}).ordered_by
	    values['patient_ref'] = self.browse(cr, uid, rec, context={}).patient_ref
	    values['order_instructions'] = self.browse(cr, uid, rec, context={}).order_instructions
	    values['order_state'] = self.browse(cr, uid, rec, context={}).order_state
	    values['partner_invoice_id'] = self.browse(cr, uid, rec, context={}).partner_invoice_id
	    values['order_type'] = self.browse(cr, uid, rec, context={}).order_type
	    values['order_payment_date'] = self.browse(cr, uid, rec, context={}).order_payment_date
	    values['payment_notes'] = self.browse(cr, uid, rec, context={}).payment_notes

      
            #raise osv.except_osv(_('Expecting an Agency Code'),_('IP adress is: %s' % patientid))
            for item in values:
                if (values[item] is None) or (values[item] is False):
                    values[item] = " "
            #raise osv.except_osv(_('Expecting an Agency Code'),_('ids numbers: %s' % ids))
            if prescriptionRef != 0:
                try:
                    connect_write(ip_address, port, username, password, database, patientid, values, identifier_type,update_type)
                    super(sale_order_prescription, self).write(cr, uid, rec, {'for_synchronization': False}, context={})
                except:
                    super(sale_order_prescription, self).write(cr, uid, rec, {'for_synchronization': True}, context={})
            else:
                try:
                    id_openmrs = connect(ip_address, port, username, password, database, values, identifier_type,update_type)
                    super(sale_order_prescription, self).write(cr, uid, rec, {'openmrs_number': id_openmrs}, context={})
                    super(sale_order_prescription, self).write(cr, uid, rec, {'for_synchronization': False}, context={})

                except:
                    super(sale_order_prescription, self).write(cr, uid, rec, {'for_synchronization': True}, context={})

        return True

        
  

sale_order_prescription ()






class openmrs_prescription_connection(osv.osv):
	def sync_Order(self, cr, uid, *args):
		syncIds = self.pool.get('sale.order').search(cr, uid, [('for_synchronization', '=', True)], offset=0, limit=None, order=None, context=None, count=False)
		self.pool.get('sale.order').write(cr, uid, syncIds, {}, context={})
		raise osv.except_osv(_('Synchronization:'),_('Complete'))

	_name = "openmrs.order.connect"
	_columns = {
        'ip_address' : fields.char ('ip_address', size=50, help='IP address of your OpenMRS mysql server' ),
        'port' : fields.char ('port', size=50, help='port of your OpenMRS mysql server'),
        'username' : fields.char ('username', size=50, help='Username of your OpenMRS mysql server'),
        'password' :fields.char ('password', size=50, help='Password of your OpenMRS mysql server'),
        'database' :fields.char ('database', size=50, help='Database of OpenMRS in your mysql server'),
        'identifier_type' : fields.integer('identifier_type', help='ID of the identifier type \n Ex. 2 for Old OpenMRS Identifier'),
    }

openmrs_prescription_connection()

