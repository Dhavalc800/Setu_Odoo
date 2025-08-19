/** @odoo-module **/

const { Component } = owl;
import { registry } from '@web/core/registry';

export class TataTeleServiceContainer extends Component {}

Object.assign(TataTeleServiceContainer, {
    template: 'web.TataTeleService',
});

registry.category('actions').add('tata_tele_service', TataTeleServiceContainer);