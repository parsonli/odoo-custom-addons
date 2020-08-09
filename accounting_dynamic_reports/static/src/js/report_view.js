odoo.define('accounting_dynamic_reports.MyReportWidget', function (require) {
    'use strict';
    var core = require('web.core');
    var ControlPanelMixin = require('web.ControlPanelMixin');
    var QWeb = core.qweb;
    var rpc = require('web.rpc');
    var AbstractAction = require('web.AbstractAction');

    var report_bs_view = AbstractAction.extend(ControlPanelMixin, {
        events: {
            'dblclick .categ': 'line_click'
        },

        /*returns the id of parent record based on its type*/
        get_parent_selector: function (record){
            return (record['type'] == 'account') ? record['a_id'] : record['id'];
        },

        /*this function will be evoked when we click a line in the report
        we will find the complete details of the clicked line and its childs
        we need to consider mainly two types,
        account and journal item.
        for 'account', its childs will be in this.journal_items array
        and for 'journal items' we don't need to find the childs

        we will pass the parent and child details to another function for updating the details
        in the view.
        */
        find_child: function (el, line, line_type, self) {
            var category = self.category;
            var journal_items = self.journal_items;
            var current_line;
            var childs = [];
            if (line_type != 'journal_item' && line_type != 'account'){
                for (var i in category){
                    if(category[i]['id'] == line){
                        current_line = category[i];
                        break;
                    }
                }
                if(current_line){
                    for (var i in category){
                        if(category[i]['parent'] == line){
                            childs.push(category[i]);
                        }
                    }
                }
            }
            else if (line_type == 'account'){
                for (var i in category){
                    if(category[i]['a_id'] == line){
                        current_line = category[i];
                        break;
                    }
                }
                if(current_line){
                    for (var i in journal_items){
                        if(journal_items[i] && (journal_items[i]['p_id'] == line)){
                            childs.push(journal_items[i]);
                        }
                    }
                }
            }
            var line_detail = {
                    'parent': current_line,
                    'child': childs,
            };
            self.update_lines(el, line, line_detail);
        },

        // clicking on each line
        line_click: function (e) {
            var self = this;
            var line = $(e.target).data('id');
            // based on this line_type, we will decide that we are clicked on journal items or not
            var line_type = $(e.target).data('type');
            if (line_type == 'journal_item'){
                for (var j in self.journal_items){
                    if(self.journal_items[j]['id'] == line){
                        self.do_action({
                            type: 'ir.actions.act_window',
                            res_model: "account.move",
                            res_id: self.journal_items[j]['j_id'],
                            views: [[false, 'form']],
                        });
                    }
                }
            }
            else{
                self.find_child($(e.target), line, line_type, self);
            }

            return;
        },

        /*This function will create a row(<tr></tr>) of the provided record and returns it.
            It will be used to replace the old one.
        */
        find_parent_row: function(parent){
            var temp_str = "";
            var attr = "";
            var rec_id = this.get_parent_selector(parent);


            attr = " id="+String(rec_id)+" data-id=" + String(rec_id) + " data-type=" + parent['type'];
            temp_str += "<tr class='child_row' data-id="+String(rec_id)+" id="+String(rec_id)+">";
            /*need to apply the styles based on the type
            so, calling another function to create the columns and apply styles*/
            temp_str += this.create_lines_with_style(parent, attr);
            temp_str += "</tr>";
            return temp_str;
        },

        get_childs_records: function(record, id){
        /*finding the childs of the current record based on its type
         i.e, journal item or account or report
         For type 'account', we need to find the childs from a different location
         */
            var category = this.category;
            var journal_items = this.journal_items;
            var childs = [];
            if (record['type'] != 'journal_item' && record['type'] != 'account'){
                for (var i in category){
                    if(category[i]['parent'] == id){
                        childs.push(category[i]);
                    }
                }
            }
            else if (record['type'] == 'account'){
                for (var i in journal_items){
                    if(journal_items[i] && (journal_items[i]['p_id'] == id)){
                        childs.push(journal_items[i]);
                    }
                }
            }
            return childs;
        },

        /*this function will find and remove all the child rows of the selected parent
        It is needed when we are clicking for the second time on the same lin to fold it.*/
        remove_childs: function(rec){
            var self = this;
            var rec_id = this.get_parent_selector(rec);
            var childs = this.get_childs_records(rec, rec_id);
            if(childs.length > 0){
                for(var j in childs){
                    var child_id = this.get_parent_selector(childs[j]);
                    $("tr#"+child_id).remove();
                    //need to update the status of already created childs, which we are going to remove
                    for (var k in self.category){
                        var categ_id = self.get_parent_selector(self.category[k]);
                        if((categ_id == child_id) && (self.category[k]['fold'] == true)){
                            self.category[k]['fold'] = false;
                        }
                        else if(categ_id == child_id){
                            self.category[k]['fold'] = true;
                        }
                    }
                    self.remove_childs(childs[j]);
                }
            }
        },

        create_lines_with_style: function(rec, attr){
            //creating columns with styles based on the type
            var temp_str = "";

            if(rec['type'] == 'journal_item'){
                var style_name = "font-size:13px!important;padding-left:55px!important; border-bottom:none !important;";
                var style_bal = "font-size:15px;";
                var attr_name = attr + " style="+style_name;
                var attr_bal = attr + " style="+style_bal;

                //add name
                temp_str += "<td class='child_col_name' "+attr_name+" >"+rec['name'] + "</td>";
                //add balance and debit credit colums
                if (this.form.debit_credit == true) {
                    // debit
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['debit'].toFixed(2)+
                        "</td>";
                    // credit
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['credit'].toFixed(2)+
                        "</td>";
                    // balance
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['balance'].toFixed(2)+"</td></tr>";
                }
                else {
                    temp_str += "<td class='child_col_bal' "+attr+" >"+
                        this.currency + " " + rec['balance'].toFixed(2)+
                        "</td><td class='child_col_bal' "+attr_bal+"></td></tr>";
                }
            }
            else {
                var style_name = "font-size:20px;font-weight:bold!important;padding-left:" + rec['level'] * 7 + "px!important;";
                var style_bal = "font-size:20px;";
                var attr_name = attr + " style="+style_name;
                var attr_bal = attr + " style="+style_bal;

                //add name
                temp_str += "<td class='child_col_name' "+attr_name+" >"+
                    rec['name'] + "</td>";
                //add balance and debit credit colums
                if (this.form.debit_credit == true) {
                    // debit
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['debit'].toFixed(2)+
                        "</td>";
                    // credit
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['credit'].toFixed(2)+
                        "</td>";
                    // balance
                    temp_str += "<td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['balance'].toFixed(2)+"</td></tr>";
                }
                else {
                    temp_str += "<td class='child_col_bal' "+
                        attr+"></td><td class='child_col_bal' "+attr_bal+" >"+
                        this.currency + " " + rec['balance'].toFixed(2)+"</td></tr>";
                }
            }
            return temp_str;
        },
        create_table_entry: function (child, rec_id){
            /*this function is used to create a table row
            input: row data and data-id
            output: query to create table row*/
            var temp_str = "";
            var attr = "";
            /*this attributes will decide the type and properties of the row,
            will be needed in capturing the click*/
            attr += " data-id=" + String(rec_id) + " id="+ String(rec_id) + " data-type=" + child['type'];
            temp_str += "<tr class='child_row' data-id="+String(rec_id)+" id="+String(rec_id)+">";
            temp_str += this.create_lines_with_style(child, attr);
            temp_str += "</tr>";
            return temp_str;
        },

        /*Updates the contents in the page*/
        update_lines: function (el, line, details) {
            var self = this;
            var parent = details['parent'];
            var childs = details['child'];
            var tmp = '';
            if (parent){
                var parent_selector = self.get_parent_selector(parent);
                for (var i in self.category){
                    var cur_id = (self.category[i]['type'] == 'account') ? self.category[i]['a_id'] : self.category[i]['id'];
                    if(cur_id == parent_selector){
                        if(self.category[i]['fold'] == true){
                            self.category[i]['fold'] = false;
                            parent['fold'] = false;
                        }
                        else {
                            self.category[i]['fold'] = true;
                            parent['fold'] = true;
                        }
                        break;
                    }
                }
                // first click
                if(parent['fold'] == false && childs.length > 0){
                    for(var l in childs){
                        var rec = childs[l];
                        var r_id = self.get_parent_selector(rec);
//                        creating the table row and appending the contents
                        var rec_class='child';
                        tmp += self.create_table_entry(rec, r_id);
                    }

                    var final_el = self.find_parent_row(parent);
                    $("tr#"+parent_selector).replaceWith(final_el+tmp);
                }
                // second click on root
                else if(parent && parent['fold'] == true && parent['parent'] == false){
                    tmp += self.find_parent_row(parent);;
//                  folding the row
                    $("tr#"+parent_selector).replaceWith(tmp);
                    // need to remove the childs
                    self.remove_childs(parent);
                }
                // second click on childs
                else if(parent && parent['fold'] == true){
                    tmp += self.find_parent_row(parent);
                    self.remove_childs(parent);
                    $("tr#"+parent_selector).replaceWith(tmp);

                }
            }
            return;
        },
        init: function(parent, action) {
            $( ".main_report" ).empty();
            this.category = {};
            this.report_name = action.report_name;
            //id of parent
            this.id = action.id;
            this.parent = action.parent;
            this.report_id = action.report_id;
            var lines = action.report_lines;
            this.form = action.form;
            for (var l in lines){
                lines[l]['fold'] = true;
            }
            this.category = lines;
            this.currency = action.currency;
            this.journal_items = action.journal_items;
            return this._super.apply(this, arguments);
        },
        renderElement: function () {
            this._super();
            var self = this;

            var first_childs = this.get_childs_records(self.parent, self.id);
            for (var c in first_childs) {
                first_childs[c]['balance_r'] =
                    first_childs[c]['balance'] ? first_childs[c]['balance'].toFixed(2): 0.00;
                first_childs[c]['debit_r'] =
                    first_childs[c]['debit'] ? first_childs[c]['debit'].toFixed(2): 0.00;
                first_childs[c]['credit_r'] =
                    first_childs[c]['credit'] ? first_childs[c]['credit'].toFixed(2): 0.00;
            }
            var date_str = 'Showing ' + self.form['target_move'] + " moves ";
            if(self.form['date_from']){
                date_str += " from " + String(self.form['date_from']);
            }
            if(self.form['date_to']){
                date_str += " to " + String(self.form['date_to']);
            }
            var $content = $(QWeb.render("report_financial", {
                    heading: self.report_name,
                    currency: self.currency,
                    first_childs: first_childs,
                    id: self.id,
                    type: 'report',
                    date_str: date_str,
                    debit_credit: self.form['debit_credit']
            }));
            self.$el.html($content);
            return ;
        },
    });
    core.action_registry.add("report_bs_view", report_bs_view);
    return report_bs_view;
});
