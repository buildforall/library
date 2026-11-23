#include "curve_service.hpp"

#include <cstring>

#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "host/ble_hs.h"
#include "host/util/util.h"
#include "nimble/nimble_port.h"
#include "nimble/nimble_port_freertos.h"
#include "services/gap/ble_svc_gap.h"
#include "services/gatt/ble_svc_gatt.h"

namespace curve_service {
namespace {

const char *TAG = "curve";

// UUIDs, least significant byte first
const ble_uuid128_t kServiceUuid = BLE_UUID128_INIT(
    0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x9a, 0x1d, 0x4b, 0xa0, 0xbf, 0x00, 0x08, 0x4b, 0x6e);
const ble_uuid128_t kCurveUuid = BLE_UUID128_INIT(
    0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x10, 0x9a, 0x1d, 0x4b, 0xa0, 0xbf, 0x01, 0x08, 0x4b, 0x6e);

uint16_t curve_handle;
uint16_t conn_handle = BLE_HS_CONN_HANDLE_NONE;
uint8_t own_addr_type;
int16_t last_packet[16];
uint16_t last_len;

int curve_access(uint16_t, uint16_t, ble_gatt_access_ctxt *ctxt, void *) {
    if (ctxt->op == BLE_GATT_ACCESS_OP_READ_CHR)
        return os_mbuf_append(ctxt->om, last_packet, last_len) == 0 ? 0 : BLE_ATT_ERR_INSUFFICIENT_RES;
    return BLE_ATT_ERR_UNLIKELY;
}

ble_gatt_chr_def characteristics[2];
ble_gatt_svc_def services[2];

void advertise();

int on_gap(ble_gap_event *event, void *) {
    switch (event->type) {
    case BLE_GAP_EVENT_CONNECT:
        if (event->connect.status == 0) conn_handle = event->connect.conn_handle;
        else advertise();
        break;
    case BLE_GAP_EVENT_DISCONNECT:
        conn_handle = BLE_HS_CONN_HANDLE_NONE;
        advertise();
        break;
    case BLE_GAP_EVENT_ADV_COMPLETE:
        advertise();
        break;
    default:
        break;
    }
    return 0;
}

void advertise() {
    ble_hs_adv_fields fields = {};
    fields.flags = BLE_HS_ADV_F_DISC_GEN | BLE_HS_ADV_F_BREDR_UNSUP;
    const char *name = ble_svc_gap_device_name();
    fields.name = reinterpret_cast<const uint8_t *>(name);
    fields.name_len = std::strlen(name);
    fields.name_is_complete = 1;
    ble_gap_adv_set_fields(&fields);

    ble_hs_adv_fields rsp = {};
    rsp.uuids128 = &kServiceUuid;
    rsp.num_uuids128 = 1;
    rsp.uuids128_is_complete = 1;
    ble_gap_adv_rsp_set_fields(&rsp);

    ble_gap_adv_params params = {};
    params.conn_mode = BLE_GAP_CONN_MODE_UND;
    params.disc_mode = BLE_GAP_DISC_MODE_GEN;
    int rc = ble_gap_adv_start(own_addr_type, nullptr, BLE_HS_FOREVER, &params, on_gap, nullptr);
    if (rc != 0 && rc != BLE_HS_EALREADY) ESP_LOGW(TAG, "advertising failed: %d", rc);
}

void on_sync() {
    ble_hs_util_ensure_addr(0);
    ble_hs_id_infer_auto(0, &own_addr_type);
    advertise();
}

void host_task(void *) {
    nimble_port_run();
    nimble_port_freertos_deinit();
}

}  // namespace

void start(const char *device_name) {
    if (nimble_port_init() != ESP_OK) {
        ESP_LOGE(TAG, "NimBLE init failed");
        return;
    }
    characteristics[0] = {};
    characteristics[0].uuid = &kCurveUuid.u;
    characteristics[0].access_cb = curve_access;
    characteristics[0].flags = BLE_GATT_CHR_F_READ | BLE_GATT_CHR_F_NOTIFY;
    characteristics[0].val_handle = &curve_handle;
    characteristics[1] = {};

    services[0] = {};
    services[0].type = BLE_GATT_SVC_TYPE_PRIMARY;
    services[0].uuid = &kServiceUuid.u;
    services[0].characteristics = characteristics;
    services[1] = {};

    ble_svc_gap_init();
    ble_svc_gatt_init();
    ble_gatts_count_cfg(services);
    ble_gatts_add_svcs(services);
    ble_svc_gap_device_name_set(device_name);
    ble_hs_cfg.sync_cb = on_sync;
    nimble_port_freertos_init(host_task);
}

void send(const float *volume_l, const float *flow_lps, int n) {
    for (int i = 0; i < n; i += 5 * 8) {
        int m = 0;
        for (int j = i; j < n && m < 16; j += 5) {
            last_packet[m++] = static_cast<int16_t>(volume_l[j] * 1000);
            last_packet[m++] = static_cast<int16_t>(flow_lps[j] * 1000);
        }
        last_len = m * sizeof(int16_t);
        if (conn_handle != BLE_HS_CONN_HANDLE_NONE) {
            os_mbuf *om = ble_hs_mbuf_from_flat(last_packet, last_len);
            if (om) ble_gatts_notify_custom(conn_handle, curve_handle, om);
            vTaskDelay(pdMS_TO_TICKS(8));
        }
    }
}

}  // namespace curve_service
