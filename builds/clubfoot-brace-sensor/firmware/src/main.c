/*
 * Clubfoot brace adherence sensor, Zephyr RTOS on a Seeed XIAO nRF52840.
 *
 * Every 10 minutes: one-shot TMP117 reading, appended as one byte to a file
 * on the internal flash (LittleFS). Press the button to advertise over
 * Bluetooth for 2 minutes. Commands written to the control characteristic:
 * "S" daily summary, "D" raw dump, "C" clear the log.
 */

#include <string.h>

#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/i2c.h>
#include <zephyr/fs/fs.h>
#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/sys/byteorder.h>

#include "wearlog.h"

LOG_MODULE_REGISTER(brace, LOG_LEVEL_INF);

#define SAMPLE_PERIOD K_MINUTES(10)
#define ADVERTISE_FOR K_SECONDS(120)
#define LOG_PATH      "/lfs/wear.bin"

static const struct i2c_dt_spec tmp117 = I2C_DT_SPEC_GET(DT_NODELABEL(tmp117));
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET(DT_ALIAS(sw0), gpios);
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);
static struct gpio_callback button_cb;

/* ------------------------------------------------------------ temperature */

static int tmp117_one_shot(float *celsius)
{
	/* CONFIG: one-shot conversion (MOD=11), 8 averages (AVG=01) */
	uint8_t cfg[3] = {0x01, 0x0C, 0x20};
	uint8_t reg = 0x00, raw[2];
	int err = i2c_write_dt(&tmp117, cfg, sizeof(cfg));

	if (err) {
		return err;
	}
	k_msleep(130);
	err = i2c_write_read_dt(&tmp117, &reg, 1, raw, sizeof(raw));
	if (err) {
		return err;
	}
	*celsius = (int16_t)sys_get_be16(raw) * 0.0078125f;
	return 0;
}

/* ------------------------------------------------------------ log file */

static int log_append(uint8_t b)
{
	struct fs_file_t f;
	int err;

	fs_file_t_init(&f);
	err = fs_open(&f, LOG_PATH, FS_O_CREATE | FS_O_APPEND | FS_O_WRITE);
	if (err) {
		return err;
	}
	err = fs_write(&f, &b, 1);
	fs_close(&f);
	return err < 0 ? err : 0;
}

/* Reads the whole log into buf. At 144 bytes a day, 8 KB holds eight weeks. */
static uint8_t log_buf[8192];

static ssize_t log_read_all(void)
{
	struct fs_file_t f;
	ssize_t n;

	fs_file_t_init(&f);
	if (fs_open(&f, LOG_PATH, FS_O_READ)) {
		return 0;
	}
	n = fs_read(&f, log_buf, sizeof(log_buf));
	fs_close(&f);
	return n < 0 ? 0 : n;
}

/* ------------------------------------------------------------ Bluetooth */

#define BRACE_UUID(n) BT_UUID_128_ENCODE(0x6e4b0900 + (n), 0xbfa0, 0x4b1d, 0x9a10, 0x000000000009ULL)

static const struct bt_uuid_128 svc_uuid = BT_UUID_INIT_128(BRACE_UUID(0));
static const struct bt_uuid_128 ctrl_uuid = BT_UUID_INIT_128(BRACE_UUID(1));
static const struct bt_uuid_128 data_uuid = BT_UUID_INIT_128(BRACE_UUID(2));

static char pending_cmd;
static void command_handler(struct k_work *work);
static K_WORK_DEFINE(command_work, command_handler);

static ssize_t ctrl_write(struct bt_conn *conn, const struct bt_gatt_attr *attr, const void *buf,
			  uint16_t len, uint16_t offset, uint8_t flags)
{
	if (len) {
		pending_cmd = ((const char *)buf)[0];
		k_work_submit(&command_work);   /* file reads stay off the Bluetooth thread */
	}
	return len;
}

static void data_ccc_changed(const struct bt_gatt_attr *attr, uint16_t value)
{
}

BT_GATT_SERVICE_DEFINE(brace_svc,
	BT_GATT_PRIMARY_SERVICE(&svc_uuid),
	BT_GATT_CHARACTERISTIC(&ctrl_uuid.uuid, BT_GATT_CHRC_WRITE, BT_GATT_PERM_WRITE, NULL,
			       ctrl_write, NULL),
	BT_GATT_CHARACTERISTIC(&data_uuid.uuid, BT_GATT_CHRC_NOTIFY, BT_GATT_PERM_NONE, NULL,
			       NULL, NULL),
	BT_GATT_CCC(data_ccc_changed, BT_GATT_PERM_READ | BT_GATT_PERM_WRITE),
);

/* Chunks of 20 bytes reach every phone, whatever MTU it negotiates. */
static void send_text(const char *s, size_t len)
{
	for (size_t i = 0; i < len; i += 20) {
		bt_gatt_notify(NULL, &brace_svc.attrs[4], s + i, MIN(20, len - i));
		k_msleep(10);
	}
}

static void emit_line(const struct wear_summary *s, void *ctx)
{
	char line[32];

	send_text(line, wear_format(s, line, sizeof(line)));
}

static void command_handler(struct k_work *work)
{
	static const char header[] = "day,hours_worn\n";
	ssize_t n;

	switch (pending_cmd) {
	case 'S':
		send_text(header, sizeof(header) - 1);
		n = log_read_all();
		if (n == 0) {
			send_text("no data\n", 8);
		}
		wear_summarise(log_buf, n, emit_line, NULL);
		break;
	case 'D': {
		char line[64];
		size_t len = 0;

		n = log_read_all();
		for (ssize_t i = 0; i < n; i++) {
			int q = log_buf[i];   /* x.yz without floating-point printf */
			len += snprintk(line + len, sizeof(line) - len, "%d.%02d%c", 10 + q / 4,
					(q % 4) * 25, (i % 6 == 5) ? '\n' : ',');
			if (len > 48) {
				send_text(line, len);
				len = 0;
			}
		}
		send_text(line, len);
		send_text("\n", 1);
		break;
	}
	case 'C':
		fs_unlink(LOG_PATH);
		send_text("cleared\n", 8);
		break;
	}
}

static const struct bt_data ad[] = {
	BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
	BT_DATA_BYTES(BT_DATA_UUID128_ALL, BRACE_UUID(0)),
};
static const struct bt_data sd[] = {
	BT_DATA(BT_DATA_NAME_COMPLETE, CONFIG_BT_DEVICE_NAME, sizeof(CONFIG_BT_DEVICE_NAME) - 1),
};

static void stop_advertising(struct k_work *work)
{
	bt_le_adv_stop();
}
static K_WORK_DELAYABLE_DEFINE(adv_timeout, stop_advertising);

static void start_advertising(struct k_work *work)
{
	int err = bt_le_adv_start(BT_LE_ADV_CONN_FAST_1, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));

	if (err && err != -EALREADY) {
		LOG_WRN("advertising failed (%d)", err);
		return;
	}
	k_work_reschedule(&adv_timeout, ADVERTISE_FOR);
}
static K_WORK_DEFINE(adv_work, start_advertising);

static void button_pressed(const struct device *dev, struct gpio_callback *cb, uint32_t pins)
{
	k_work_submit(&adv_work);
}

/* ------------------------------------------------------------ main */

int main(void)
{
	int err;

	if (!i2c_is_ready_dt(&tmp117) || !gpio_is_ready_dt(&button) || !gpio_is_ready_dt(&led)) {
		LOG_ERR("hardware not ready");
		return 0;
	}
	gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	gpio_pin_configure_dt(&button, GPIO_INPUT);
	gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
	gpio_init_callback(&button_cb, button_pressed, BIT(button.pin));
	gpio_add_callback(button.port, &button_cb);

	err = bt_enable(NULL);
	if (err) {
		LOG_ERR("Bluetooth init failed (%d)", err);
	}

	for (;;) {
		float t;

		if (tmp117_one_shot(&t) == 0) {
			err = log_append(wear_encode(t));
			if (err) {
				LOG_WRN("log write failed (%d)", err);
			}
		}
		gpio_pin_set_dt(&led, 1);   /* 20 ms blink: still alive */
		k_msleep(20);
		gpio_pin_set_dt(&led, 0);
		k_sleep(SAMPLE_PERIOD);
	}
	return 0;
}
