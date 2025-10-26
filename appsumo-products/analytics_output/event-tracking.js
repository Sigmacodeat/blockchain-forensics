// Client-side event tracking

// license_activated
gtag('event', 'license_activated', {
          'event_category': 'conversion',
          'event_label': 'appsumo',
          'value': tier_price,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': tier
        });

// feature_used
gtag('event', 'feature_used', {
          'event_category': 'engagement',
          'event_label': feature_name,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': user_tier
        });

// tier_upgrade
gtag('event', 'tier_upgrade', {
          'event_category': 'conversion',
          'event_label': 'upsell',
          'value': upgrade_price,
          'custom_parameter_1': product_slug,
          'custom_parameter_2': old_tier + '_to_' + new_tier
        });
