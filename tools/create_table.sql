CREATE DATABASE IF NOT EXISTS catalyst_meraki;

USE catalyst_meraki;

CREATE TABLE IF NOT EXISTS switch (
    id VARCHAR(255) NOT NULL,
    platform VARCHAR(255) NOT NULL,
    model VARCHAR(255) NOT NULL,
    modular BOOLEAN NOT NULL,
    network_module VARCHAR(255),
    tier VARCHAR(255),
    dl_ge INTEGER,
    dl_ge_poe INTEGER,
    dl_ge_poep INTEGER,
    dl_ge_upoe INTEGER,
    dl_ge_upoep INTEGER,
    dl_ge_sfp INTEGER,
    dl_2ge_upoe INTEGER,
    dl_mgig_poep INTEGER,
    dl_mgig_upoe INTEGER,
    dl_10ge INTEGER,
    dl_10ge_sfpp INTEGER,
    dl_25ge_sfp28 INTEGER,
    dl_40ge_qsfpp INTEGER,
    dl_100ge_qsfp28 INTEGER,
    ul_ge_sfp INTEGER,
    ul_mgig INTEGER,
    ul_10ge_sfpp INTEGER,
    ul_25ge_sfp28 INTEGER,
    ul_40ge_qsfpp INTEGER,
    ul_100ge_qsfp28 INTEGER,
    poe_power INTEGER,
    switching_capacity INTEGER,
    stackable BOOLEAN,
    mac_entry INTEGER,
    vlan INTEGER,
    note VARCHAR(255),
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS mapping (
    id INTEGER NOT NULL AUTO_INCREMENT,
    catalyst VARCHAR(255) NOT NULL,
    meraki VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) NOT NULL,
    privilege VARCHAR(255) NOT NULL,
    PRIMARY KEY (id)
)
