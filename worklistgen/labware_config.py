LABWARE_TYPES = {
    '96wellplate': {
        'layout': [f'{row}{col}' for col in range(1, 13) for row in 'ABCDEFGH'],
        'volume': 200
    },
    'tuberack': {
        'layout': [f'{row}{col}' for row in 'AB' for col in range(1, 24)],
        'volume': 1500
    }
}