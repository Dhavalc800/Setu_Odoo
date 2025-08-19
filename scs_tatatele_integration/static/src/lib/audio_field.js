/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, useState, onWillUpdateProps } from "@odoo/owl";

export class AudioField extends Component {}

AudioField.template = "web.AudioField";
AudioField.props = {
    ...standardFieldProps,
};

AudioField.supportedTypes = ["char"];

registry.category("fields").add("audio_field", AudioField);
