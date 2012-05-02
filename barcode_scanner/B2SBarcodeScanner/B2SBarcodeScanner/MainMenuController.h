//
//  MainMenuController.h
//  B2SBarcodeScanner
//
//  Created by Ding Nicholas on 12/30/11.
//  Copyright (c) 2011 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

enum ActionType {
    ActionTypeAdd = 0,
    ActionTypeRemove = 2,
    ActionTypeReturn = 3
};

@interface MainMenuController : UIViewController <ZBarReaderViewDelegate, UIActionSheetDelegate> {
    NSString *barcode;
    BOOL isLoading;
}

@property (retain, nonatomic) IBOutlet UISegmentedControl *requestTypeControl;
@property (retain, nonatomic) IBOutlet UILabel *shopLabel;
@property (retain, nonatomic) IBOutlet ZBarReaderView *barReaderView;

- (void)presentActionSheet:(NSString *)code;
- (void)requestWithType:(NSInteger)actionType barcode:code;

@end
