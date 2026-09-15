<?php
/**
 * Plugin Name: AstroVakta Connect
 * Description: One-click integration between your WooCommerce store and your AstroVakta site.
 * Version: 1.0.0
 */

if (!defined('ABSPATH')) exit;

class AstroVakta_Connect {
    const API_BASE = 'https://api.astrovakta.com/sites/integrations/woocommerce';

    public function __construct() {
        add_action('admin_menu', [$this, 'menu']);
        add_action('admin_post_avk_connect', [$this, 'handle_connect']);
    }

    public function menu() {
        add_submenu_page('woocommerce', 'AstroVakta Connect', 'AstroVakta Connect', 'manage_woocommerce', 'astrovakta-connect', [$this, 'page']);
    }

    public function page() { ?>
        <div class="wrap">
            <h1>AstroVakta Connect</h1>
            <p>Paste the activation key from your AstroVakta dashboard (Store → Integrations → WooCommerce one-click). We'll create secure API keys and link your store — nothing else to configure.</p>
            <form method="post" action="<?php echo admin_url('admin-post.php'); ?>">
                <input type="hidden" name="action" value="avk_connect">
                <?php wp_nonce_field('avk_connect'); ?>
                <table class="form-table">
                    <tr><th>Activation key</th>
                        <td><input type="text" name="avk_key" class="regular-text" placeholder="avk_..." required></td></tr>
                </table>
                <?php submit_button('Connect my store'); ?>
            </form>
        </div>
    <?php }

    public function handle_connect() {
        if (!current_user_can('manage_woocommerce')) wp_die('Not allowed');
        check_admin_referer('avk_connect');

        $key = sanitize_text_field($_POST['avk_key'] ?? '');
        if (!$key) wp_die('Activation key required');

        // Create dedicated REST API credentials for AstroVakta
        $data = [
            'user_id'         => get_current_user_id(),
            'description'     => 'AstroVakta Connect',
            'permissions'     => 'read_write',
            'consumer_key'    => 'ck_' . wc_rand_hash(),
            'consumer_secret' => 'cs_' . wc_rand_hash(),
        ];
        global $wpdb;
        $wpdb->insert("{$wpdb->prefix}woocommerce_api_keys", [
            'user_id'         => $data['user_id'],
            'description'     => $data['description'],
            'permissions'     => $data['permissions'],
            'consumer_key'    => wc_api_hash($data['consumer_key']),
            'consumer_secret' => $data['consumer_secret'],
            'truncated_key'   => substr($data['consumer_key'], -7),
        ]);

        // Register them with AstroVakta
        $resp = wp_remote_post(self::API_BASE . '/claim', [
            'headers' => ['Content-Type' => 'application/json'],
            'body'    => wp_json_encode([
                'activation_key' => $key,
                'shop_domain'    => parse_url(home_url(), PHP_URL_HOST),
                'api_key'        => $data['consumer_key'],
                'api_secret'     => $data['consumer_secret'],
            ]),
            'timeout' => 20,
        ]);

        if (is_wp_error($resp) || wp_remote_retrieve_response_code($resp) !== 200) {
            wp_die('Could not reach AstroVakta — check the activation key and try again.');
        }
        update_option('astrovakta_connected', true);
        wp_redirect(admin_url('admin.php?page=astrovakta-connect&connected=1'));
        exit;
    }
}

new AstroVakta_Connect();
