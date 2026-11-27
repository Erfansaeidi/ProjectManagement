ticket apis

    for user

    POST       /api/support/tickets/                          new ticket
    GET        /api/support/tickets/                           see tickets
    GET        /api/support/tickets/{id}/                     ticket detail
    POST       /api/support/tickets/{id}/messages/        massage in ticket
    GET        /api/support/tickets/{id}/messages/        conversation in ticket


    for support

    PATCH      /api/support/tickets/{id}/close/              close ticket  
    GET        /api/support/staff/tickets/                       see ticket
    PATCH      /api/support/staff/tickets/{id}/                 change ticket priority
    POST       /api/support/staff/tickets/{id}/assign/        ticket for especial support
