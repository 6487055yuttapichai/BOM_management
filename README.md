<!-- Use {Ctrl + Shift + V} for Preview Mode-->
dev in python 3.13.9

## list of contents
- [install requirements](#requirements)
- [BOM_Master table](#BOM_Master)

## requirements
This command is used to **install** all required libraries from the requirements file:
```cmd
pip install -r requirements.txt
```
This command is used to **generate (or get)** the list of currently installed libraries and save them into a requirements file:
```
pip freeze >> requirements.txt
```


## BOM_Master
### Command to create a BOM_Master table Create

```sql
CREATE TABLE dbo.bom_master (
    id serial4 PRIMARY KEY,
    item_id varchar(50) NOT NULL,
    description text,
    type varchar(10),
    nominal_tubing_size varchar(20),
    color varchar(50),
    tubing numeric(10,3),
    tubing_tolerance numeric(10,3),
    wall_thickness numeric(10,3),
    wall_thickness_tolerance numeric(10,3),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamptz,
    CONSTRAINT bom_master_item_id_key UNIQUE (item_id)
);
```

### Example of a command to insert data in to change_log

```sql
INSERT INTO dbo.bom_master (
    item_id,
    description,
    type,
    nominal_tubing_size,
    color,
    tubing,
    tubing_tolerance,
    wall_thickness,
    wall_thickness_tolerance
)
VALUES
('00654962','TUBING, PLASTIC. 1/4 OD, BLACK, SAE J844 TYPE A', 'A', '1/4', 'BLACK', 6.35, 0.08, 1.00, 0.08),
('01220011','TUBING, PLASTIC. 1/4 OD, BROWN, SAE J844 TYPE A', 'A', '1/4', 'BROWN', 6.35, 0.08, 1.00, 0.08),
('01220060','TUBING, PLASTIC. 1/4 OD, GRAY, SAE J844 TYPE A', 'A', '1/4', 'GRAY', 6.35, 0.08, 1.00, 0.08),
('01346790','TUBING, PLASTIC. 1/4 OD, GREEN, SAE J844 TYPE A', 'A', '1/4', 'GREEN', 6.35, 0.08, 1.00, 0.08),
('01346808','TUBING, PLASTIC. 1/4 OD, ORANGE, SAE J844 TYPE A', 'A', '1/4', 'ORANGE', 6.35, 0.08, 1.00, 0.08),
('01346816','TUBING, PLASTIC. 1/4 OD, YELLOW, SAE J844 TYPE A', 'A', '1/4', 'YELLOW', 6.35, 0.08, 1.00, 0.08),
('01346824','TUBING, PLASTIC. 1/4 OD, BLUE, SAE J844 TYPE A', 'A', '1/4', 'BLUE', 6.35, 0.08, 1.00, 0.08),
('01346832','TUBING, PLASTIC. 1/4 OD, RED, SAE J844 TYPE A', 'A', '1/4', 'RED', 6.35, 0.08, 1.00, 0.08)

INSERT INTO dbo.bom_master (
    item_id,
    description,
    type,
    nominal_tubing_size,
    color,
    tubing,
    tubing_tolerance,
    wall_thickness,
    wall_thickness_tolerance
)
values
('00012435','TUBING, PLASTIC. 3/8 OD, BROWN, SAE J844 TYPE B', 'B', '3/4', 'BROWN', 9.35, 0.10, 1.57, 0.10),
('00012443','TUBING, PLASTIC. 3/8 OD, GREEN, SAE J844 TYPE B', 'B', '3/4', 'GREEN', 9.35, 0.10, 1.57, 0.10),
('00012450','TUBING, PLASTIC. 3/8 OD, ORANGE, SAE J844 TYPE B', 'B', '3/4', 'ORANGE', 9.35, 0.10, 1.57, 0.10),
('00013086','TUBING, PLASTIC. 3/8 OD, GRAY, SAE J844 TYPE B', 'B', '3/4', 'GRAY', 9.35, 0.10, 1.57, 0.10),
('00989319','TUBING, PLASTIC. 3/8 OD, BLACK, SAE J844 TYPE B', 'A', '1/4', 'BLACK', 9.35, 0.10, 1.57, 0.10),
('01220037','TUBING, PLASTIC. 3/8 OD, RED, SAE J844 TYPE B', 'B', '3/4', 'RED', 9.35, 0.10, 1.57, 0.10),
('01346857','TUBING, PLASTIC. 3/8 OD, BLUE, SAE J844 TYPE B', 'B', '3/4', 'BLUE', 9.35, 0.10, 1.57, 0.10)

INSERT INTO dbo.bom_master (
    item_id,
    description,
    type,
    nominal_tubing_size,
    color,
    tubing,
    tubing_tolerance,
    wall_thickness,
    wall_thickness_tolerance
)
values
('01197177','TUBING, PLASTIC. 1/2 OD, SILVER, SAE J844 TYPE B', 'B', '1/2', 'SILVER', 12.70, 0.13, 1.57, 0.10),
('01346865','TUBING, PLASTIC. 1/2 OD, BLACK, SAE J844 TYPE B', 'B', '1/2', 'BLACK', 12.70, 0.13, 1.57, 0.10),
('01346873','TUBING, PLASTIC. 1/2 OD, BLUE, SAE J844 TYPE B', 'B', '1/2', 'BLUE', 12.70, 0.13, 1.57, 0.10),
('01346881','TUBING, PLASTIC. 1/2 OD, RED, SAE J844 TYPE B', 'B', '1/2', 'RED', 12.70, 0.13, 1.57, 0.10),

INSERT INTO dbo.bom_master (
    item_id,
    description,
    type,
    nominal_tubing_size,
    color,
    tubing,
    tubing_tolerance,
    wall_thickness,
    wall_thickness_tolerance
)
values
('01643295','TUBING, PLASTIC. 5/8 OD, BLUE, SAE J844 TYPE B', 'B', '5/8', 'BLUE', 15.88, 0.13, 2.34, 0.13),
('04760328','TUBING, PLASTIC. 5/8 OD, GREEN, SAE J844 TYPE B', 'B', '5/8', 'GREEN', 15.88, 0.13, 2.34, 0.13),
('04760330','TUBING, PLASTIC. 5/8 OD, ORANGE, SAE J844 TYPE B', 'B', '5/8', 'ORANGE', 15.88, 0.13, 2.34, 0.13),
```
