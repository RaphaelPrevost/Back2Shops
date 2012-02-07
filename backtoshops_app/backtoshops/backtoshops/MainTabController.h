//
//  MainTabController.h
//  backtoshops
//
//  Created by Ding Nicholas on 2/2/12.
//  Copyright (c) 2012 __MyCompanyName__. All rights reserved.
//

#import <UIKit/UIKit.h>

enum ButtonImageTags {
    ButtonImageTagFirst = 1,
    ButtonImageTagSecond = 2,
    ButtonImageTagThird = 3
};

@interface MainTabController : UIViewController {
    UINavigationController *navigation;
}

@property (nonatomic, strong) UIViewController *currentController;
@property (nonatomic, strong) NSMutableArray *viewControllers;
@property (nonatomic, strong) IBOutlet UIView *contentView;
@property (nonatomic, strong) IBOutlet UIView *tabbar;

- (void)presentLoginViewController:(BOOL)animated;

- (IBAction)click1st:(id)sender;
- (IBAction)click2nd:(id)sender;
- (IBAction)click3rd:(id)sender;

@end
