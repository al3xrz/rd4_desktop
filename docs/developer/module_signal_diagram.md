# Схема модулей и сигналов

Эта схема показывает основные зависимости между слоями приложения и наиболее важные UI-сигналы. Направление зависимостей остается прежним: `ui -> services -> repositories -> models/core`.

## Слои и модули

```mermaid
flowchart TB
    main["app.main<br/>старт приложения"] --> core["app.core<br/>config, database, migrations, logging"]
    main --> bootstrap["services.bootstrap<br/>ensure_initial_admin"]
    main --> uiapp["ui.application<br/>QApplication и login flow"]

    uiapp --> login["LoginWindow<br/>login_success"]
    login --> auth["AuthService"]
    uiapp --> mainwindow["MainWindow<br/>меню и страницы"]

    mainwindow --> contracts["ContractsPage<br/>реестр договоров"]
    mainwindow --> details["ContractDetailsPage<br/>карточка договора"]
    mainwindow --> medpage["MedServicesPage<br/>справочник услуг"]
    mainwindow --> userspage["UsersPage<br/>пользователи"]

    contracts --> contractdialog["ContractDialog<br/>создание и редактирование"]
    details --> payments["PaymentsPanel<br/>платежи"]
    details --> acts["ActsPanel<br/>акты"]
    acts --> actdialog["ActDialog<br/>строки услуг"]
    actdialog --> picker["MedServicePickerDialog<br/>выбор услуги"]
    actdialog --> rowdialog["ActServiceRowDialog<br/>цена, количество, скидка"]
    medpage --> meddialog["MedServiceDialog"]
    userspage --> userdialog["UserDialog / PasswordDialog"]

    contracts --> contractservice["ContractService"]
    contractdialog --> contractservice
    details --> contractservice
    payments --> paymentservice["PaymentService"]
    acts --> actservice["ActService"]
    actdialog --> actservice
    picker --> medservice["MedServiceService"]
    medpage --> medservice
    meddialog --> medservice
    userspage --> auth
    userdialog --> auth
    mainwindow --> docx["DocxService"]
    mainwindow --> reportservice["ReportService"]
    details --> docx
    acts --> docx

    contractservice --> contractrepo["ContractRepository"]
    paymentservice --> paymentrepo["PaymentRepository"]
    actservice --> actrepo["ActRepository"]
    actservice --> actrowrepo["ActMedServiceRepository"]
    actservice --> medrepo["MedServiceRepository"]
    medservice --> medrepo
    auth --> userrepo["UserRepository"]
    docx --> contractservice
    docx --> actservice
    reportservice --> actrowrepo

    contractrepo --> models["app.models<br/>Contract, Payment, Act, ActMedService, MedService, User"]
    paymentrepo --> models
    actrepo --> models
    actrowrepo --> models
    medrepo --> models
    userrepo --> models
    contractrepo --> core
    paymentrepo --> core
    actrepo --> core
    actrowrepo --> core
    medrepo --> core
    userrepo --> core
```

## Основные UI-сигналы

```mermaid
sequenceDiagram
    participant App as ui.application
    participant Login as LoginWindow
    participant Main as MainWindow
    participant Contracts as ContractsPage
    participant Details as ContractDetailsPage
    participant Payments as PaymentsPanel
    participant Acts as ActsPanel
    participant ActDialog as ActDialog
    participant Picker as MedServicePickerDialog
    participant Services as services

    App->>Login: показать окно входа
    Login->>Services: AuthService.login()
    Login-->>App: login_success(user)
    App->>Main: открыть MainWindow(user)

    Main->>Contracts: стартовая страница
    Contracts->>Services: ContractService.list_contracts()
    Contracts->>Services: ContractService.list_contract_summaries()

    Contracts-->>Contracts: search_input.textChanged -> _apply_filter()
    Contracts-->>Contracts: filters.currentIndexChanged -> _apply_filter() / reload()
    Contracts-->>Contracts: table.selectionChanged -> _update_selection()

    Contracts-->>Main: table.doubleClicked / open_button.clicked
    Main->>Details: open_contract_details(contract_id)
    Details->>Payments: создать вкладку платежей
    Details->>Acts: создать вкладку актов

    Payments-->>Payments: add_payment_button.clicked -> PaymentDialog
    Payments->>Services: PaymentService.create_payment() / create_refund() / update_payment()
    Payments->>Services: PaymentService.unpost_payment()

    Acts-->>ActDialog: create_button.clicked / open_button.clicked
    ActDialog-->>Picker: add_service_button.clicked
    Picker-->>ActDialog: accepted(selected_service)
    ActDialog->>Services: ActService.create_act() / update_act()
    ActDialog->>Services: ActService.add_service()
    Note over ActDialog,Services: Если услуга и скидка совпадают, количество увеличивается вместо новой строки.

    Details-->>Main: back_button.clicked
    Main->>Contracts: reload(), focus_contract(contract_id)
```

## Поток данных и транзакций

```mermaid
flowchart LR
    ui["UI action<br/>кнопка, меню, shortcut, signal"] --> service["Service method<br/>одна бизнес-операция"]
    service --> tx["session_scope<br/>одна транзакция"]
    tx --> repo["Repository<br/>query/create/update/soft_delete, flush"]
    repo --> orm["SQLAlchemy models"]
    orm --> sqlite["SQLite rd4.db"]
    service --> domainerr["DomainError"]
    domainerr --> uierr["UI показывает QMessageBox.warning"]
```
