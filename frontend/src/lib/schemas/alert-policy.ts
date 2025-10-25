export const alertPolicyRulesSchema = {
  type: 'object',
  additionalProperties: true,
  required: ['rules'],
  properties: {
    rules: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: true,
        required: ['id'],
        properties: {
          id: { type: 'string', pattern: '^[a-z0-9._-]+$' },
          severity: { type: 'string', enum: ['low', 'medium', 'high', 'critical'] },
          description: { type: 'string' },
          conditions: {
            type: 'array',
            minItems: 1,
            items: {
              anyOf: [
                // Legacy simple condition shape
                {
                  type: 'object',
                  required: ['field', 'op', 'value'],
                  additionalProperties: true,
                  properties: {
                    field: { type: 'string' },
                    op: { type: 'string' },
                    value: {}
                  }
                },
                // Typed condition shape
                {
                  type: 'object',
                  additionalProperties: true,
                  required: ['type'],
                  properties: {
                    type: { type: 'string', enum: ['address_match','amount_gt','label_in','country_in','bridge_event'] },
                    // address_match
                    address: { type: 'string', pattern: '^0x[a-fA-F0-9]{40}$' },
                    // amount_gt
                    field: { type: 'string' },
                    threshold: { type: 'number' },
                    // label_in
                    labels: { type: 'array', items: { type: 'string' }, minItems: 1 },
                    // country_in
                    countries: { type: 'array', items: { type: 'string' }, minItems: 1 },
                    // bridge_event
                    bridge: {
                      type: 'object',
                      additionalProperties: true,
                      properties: {
                        from_chain: { type: 'string' },
                        to_chain: { type: 'string' }
                      }
                    }
                  },
                  oneOf: [
                    { required: ['type','address'], properties: { type: { const: 'address_match' } } },
                    { required: ['type','field','threshold'], properties: { type: { const: 'amount_gt' } } },
                    { required: ['type','labels'], properties: { type: { const: 'label_in' } } },
                    { required: ['type','countries'], properties: { type: { const: 'country_in' } } },
                    { required: ['type','bridge'], properties: { type: { const: 'bridge_event' } } }
                  ]
                }
              ]
            }
          },
          actions: {
            type: 'array',
            items: { type: 'string' }
          }
        }
      }
    }
  }
} as const;
